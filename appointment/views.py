from collections import defaultdict
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db.models import Count, Prefetch, Q
from django.db.models.functions import TruncDate
from django_filters.rest_framework import DjangoFilterBackend
from appointment.services import _normalize_optional_bool
from rest_framework import generics, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404

from appointment.filters import DateFilter
from appointment.models import Appointment, AppointmentReminder
from common.paginations import CustomLimitOffsetPagination
from medicals.models import MedicalServices, Category
from users.models import Doctor, Patient
from section.models import SectionRoom
from shift.models import ExceptionDate, WeeklySchedule
from .generator import generate_time_slots, remove_occupied_slots
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentFilterSerializer,
    AppointmentStatusUpdateSerializer,
    AppointmentUpdateSerializer,
    AvailableSlotSerializer,
    NextAppointmentSerializer, 
    PatientOwnAppointmentSerializer,
    AppointmentListSerializer, 
)
from .types import AppointmentStatus, AppointmentType


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.all()

        if hasattr(user, 'doctor_profile') and user.doctor_profile:
            queryset = queryset.filter(doctor=user.doctor_profile)
        elif hasattr(user, 'patient_profile') and user.patient_profile:
            queryset = queryset.filter(patient=user.patient_profile)
        elif hasattr(user, 'receptionist_profile'):
            queryset = queryset.all()
        else:
            queryset = queryset.none()

        serializer = AppointmentFilterSerializer(data=self.request.query_params)
        if serializer.is_valid():
            filters = serializer.validated_data
            if filters.get('patient_id'):
                queryset = queryset.filter(patient_id=filters['patient_id'])
            if filters.get('doctor_id'):
                queryset = queryset.filter(doctor_id=filters['doctor_id'])
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            if filters.get('type'):
                queryset = queryset.filter(type=filters['type'])
            if filters.get('date_from'):
                queryset = queryset.filter(appointment_date__gte=filters['date_from'])
            if filters.get('date_to'):
                queryset = queryset.filter(appointment_date__lte=filters['date_to'])
            if filters.get('is_paid') is not None:
                queryset = queryset.filter(is_paid=filters['is_paid'])
            if filters.get('is_urgent') is not None:
                queryset = queryset.filter(is_urgent=filters['is_urgent'])
        
        return queryset.select_related(
            'patient', 'doctor', 'medical_service', 'section'
        ).prefetch_related('blocks', 'reminders')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AppointmentListSerializer
        elif self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        elif self.action == 'retrieve':
            return AppointmentDetailSerializer
        return AppointmentDetailSerializer
    
    @action(detail=False, methods=['get'], url_path='my-appointments')
    def my_appointments(self, request):
        """دریافت نوبت‌های کاربر جاری"""
        user = request.user
        if hasattr(user, 'patient_profile'):
            appointments = Appointment.objects.filter(patient=user.patient_profile)
        elif hasattr(user, 'doctor_profile'):
            appointments = Appointment.objects.filter(doctor=user.doctor_profile)
        else:
            return Response({"error": "شما دسترسی به این بخش ندارید"}, status=403)
        today = timezone.now().date()
        upcoming = appointments.filter(
            appointment_date__gte=today,
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]
        )
        past = appointments.filter(
            Q(appointment_date__lt=today) | Q(status=AppointmentStatus.COMPLETED)
        )
        return Response({
            'upcoming': AppointmentListSerializer(upcoming, many=True).data,
            'past': AppointmentListSerializer(past, many=True).data,
            'total': appointments.count()
        })
    
    @action(detail=False, methods=['get'], url_path='available-slots')
    def available_slots(self, request):
        """دریافت زمان‌های خالی پزشک"""
        serializer = AvailableSlotSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        doctor_id = serializer.validated_data['doctor_id']
        date = serializer.validated_data['date']
        doctor = get_object_or_404(Doctor, id=doctor_id)
        weekday = date.weekday()
        weekly_schedule = WeeklySchedule.objects.filter(
            doctor=doctor,
            weekday=weekday,
            active=True
        ).first()
        if not weekly_schedule:
            return Response({
                "message": "پزشک در این روز کاری ندارد",
                "slots": []
            })
        booked_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED, AppointmentStatus.CHECKED_IN]
        ).values_list('appointment_start_time', flat=True)
        exception = ExceptionDate.objects.filter(doctor=doctor, date=date).first()
        if exception and not exception.is_available:
            return Response({
                "message": "پزشک در این تاریخ مرخصی دارد",
                "slots": []
            })
        start_time = exception.start_time if exception and exception.start_time else weekly_schedule.start_time
        end_time = exception.end_time if exception and exception.end_time else weekly_schedule.end_time
        slot_length = weekly_schedule.slot_length or 20
        available_slots = []
        current_time = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)
        while current_time + timedelta(minutes=slot_length) <= end_datetime:
            slot_start = current_time.time()
            slot_end = (current_time + timedelta(minutes=slot_length)).time()
            if slot_start not in booked_appointments:
                available_slots.append({
                    'start_time': slot_start.strftime('%H:%M'),
                    'end_time': slot_end.strftime('%H:%M'),
                    'is_available': True
                })
            current_time += timedelta(minutes=slot_length)
        return Response({
            'doctor_id': doctor.id,
            'doctor_name': doctor.get_full_name(),
            'date': date,
            'slots': available_slots
        })
    
    @action(detail=False, methods=['post'], url_path='book')
    def book_appointment(self, request):
        """رزرو نوبت جدید توسط بیمار"""
        if not hasattr(request.user, 'patient_profile'):
            return Response(
                {"error": "فقط بیماران می‌توانند نوبت رزرو کنند"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = AppointmentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save(patient=request.user.patient_profile)
        if appointment.final_amount > 0:
            payment_result = process_appointment_payment(
                appointment_id=appointment.id,
                amount=appointment.final_amount,
                payment_method='online',
                user=request.user
            )
            return Response({
                'appointment': AppointmentDetailSerializer(appointment).data,
                'payment_url': payment_result.get('payment_url'),
                'message': 'لطفاً برای تکمیل نوبت، پرداخت را انجام دهید'
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_appointment(self, request, pk=None):
        """لغو نوبت"""
        appointment = self.get_object()
        user = request.user
        has_access = (
            (hasattr(user, 'patient_profile') and appointment.patient == user.patient_profile) or
            (hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile) or
            hasattr(user, 'receptionist_profile')
        )
        if not has_access:
            return Response(
                {"error": "شما دسترسی لغو این نوبت را ندارید"},
                status=status.HTTP_403_FORBIDDEN
            )
        if not appointment.is_upcoming():
            return Response(
                {"error": "امکان لغو این نوبت وجود ندارد"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = AppointmentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment.cancel(reason=serializer.validated_data.get('cancellation_reason'))
        return Response({
            'message': 'نوبت با موفقیت لغو شد',
            'appointment': AppointmentDetailSerializer(appointment).data
        })
    
    @action(detail=True, methods=['post'], url_path='reschedule')
    def reschedule_appointment(self, request, pk=None):
        """تغییر زمان نوبت"""
        appointment = self.get_object()
        new_date = request.data.get('appointment_date')
        new_time = request.data.get('appointment_start_time')
        if not new_date or not new_time:
            return Response(
                {"error": "لطفاً تاریخ و زمان جدید را وارد کنید"},
                status=status.HTTP_400_BAD_REQUEST
            )
        overlapping = Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=new_date,
            appointment_start_time=new_time,
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]
        ).exclude(id=appointment.id)
        if overlapping.exists():
            return Response(
                {"error": "زمان انتخابی قبلاً رزرو شده است"},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.appointment_date = new_date
        appointment.appointment_start_time = new_time
        appointment.status = AppointmentStatus.RESCHEDULED
        appointment.save()
        appointment.blocks.all().delete()
        self.create_appointment_blocks(appointment)
        return Response({
            'message': 'زمان نوبت با موفقیت تغییر کرد',
            'appointment': AppointmentDetailSerializer(appointment).data
        })
    
    @action(detail=True, methods=['post'], url_path='check-in')
    def check_in(self, request, pk=None):
        """ثبت مراجعه بیمار (برای منشی/پزشک)"""
        appointment = self.get_object()
        if appointment.status != AppointmentStatus.CONFIRMED:
            return Response(
                {"error": "فقط نوبت‌های تایید شده قابلیت مراجعه دارند"},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.check_in()
        return Response({
            'message': 'مراجعه بیمار ثبت شد',
            'appointment': AppointmentDetailSerializer(appointment).data
        })
    
    @action(detail=True, methods=['post'], url_path='start-visit')
    def start_visit(self, request, pk=None):
        """شروع ویزیت (برای پزشک)"""
        appointment = self.get_object()
        if not hasattr(request.user, 'doctor_profile') or appointment.doctor != request.user.doctor_profile:
            return Response(
                {"error": "فقط پزشک مربوطه می‌تواند ویزیت را شروع کند"},
                status=status.HTTP_403_FORBIDDEN
            )
        appointment.start_visit()
        return Response({
            'message': 'ویزیت شروع شد',
            'appointment': AppointmentDetailSerializer(appointment).data
        })
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_appointment(self, request, pk=None):
        """اتمام ویزیت"""
        appointment = self.get_object()
        appointment.complete()
        return Response({
            'message': 'ویزیت به پایان رسید',
            'appointment': AppointmentDetailSerializer(appointment).data
        })
    
    @action(detail=True, methods=['post'], url_path='payment')
    def process_payment(self, request, pk=None):
        """پرداخت هزینه نوبت"""
        appointment = self.get_object()
        if appointment.is_paid:
            return Response(
                {"error": "هزینه این نوبت قبلاً پرداخت شده است"},
                status=status.HTTP_400_BAD_REQUEST
            )
        payment_method = request.data.get('payment_method', 'online')
        payment_result = process_appointment_payment(
            appointment_id=appointment.id,
            amount=appointment.final_amount,
            payment_method=payment_method,
            user=request.user
        )
        return Response(payment_result)
    
    @action(detail=False, methods=['get'], url_path='calendar')
    def doctor_calendar(self, request):
        """تقویم نوبت‌های پزشک"""
        doctor_id = request.query_params.get('doctor_id')
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        if not doctor_id:
            return Response({"error": "doctor_id الزامی است"}, status=400)
        appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date__year=year,
            appointment_date__month=month
        )
        calendar_data = {}
        for appointment in appointments:
            day = appointment.appointment_date.day
            if day not in calendar_data:
                calendar_data[day] = []
            calendar_data[day].append({
                'id': appointment.id,
                'time': appointment.appointment_start_time.strftime('%H:%M'),
                'patient': appointment.patient.get_full_name(),
                'status': appointment.status
            })
        return Response(calendar_data)
    
    @action(detail=True, methods=['post'], url_path='send-reminder')
    def send_reminder(self, request, pk=None):
        """ارسال یادآوری برای بیمار"""
        appointment = self.get_object()
        reminder_type = request.data.get('reminder_type', 'sms')
        AppointmentReminder.objects.create(
            appointment=appointment,
            reminder_type=reminder_type,
            status='sent'
        )
        appointment.reminder_sent = True
        appointment.save()
        return Response({'message': f'یادآوری از طریق {reminder_type} ارسال شد'})


class AppointmentsMonthRangeAPIView(APIView):
    def get(self, request):
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        doctor_id = request.query_params.get("doctor_id")
        if not start_date_str or not end_date_str:
            return Response({"detail": "پارامترهای start_date و end_date الزامی هستند"}, status=400)
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "فرمت تاریخ باید YYYY-MM-DD باشد"}, status=400)
        if start_date > end_date:
            return Response({"detail": "start_date نمی‌تواند بعد از end_date باشد"}, status=400)
        doctors = Doctor.objects.all()
        if doctor_id:
            doctors = doctors.filter(id=doctor_id)
            if not doctors.exists():
                return Response({"detail": "پزشک یافت نشد"}, status=404)
        doctors = list(
            doctors.select_related("base_user", "base_user").prefetch_related(
                "schedules_dr",
                "exceptions",
            )
        )
        doctor_schedule_map = {}
        doctor_exception_map = {}
        for doctor in doctors:
            schedule_by_weekday = {}
            for schedule in doctor.schedules_dr.all():
                if schedule.weekday is None:
                    continue
                schedule_by_weekday.setdefault(schedule.weekday, schedule)
            doctor_schedule_map[doctor.id] = schedule_by_weekday
            exception_by_date = {}
            for exception in doctor.exceptions.all():
                if exception.date is None:
                    continue
                exception_by_date.setdefault(exception.date, exception)
            doctor_exception_map[doctor.id] = exception_by_date
        occupied_slots_map = defaultdict(set)
        occupied_slots_qs = Appointment.objects.filter(
            appointment_date__range=[start_date, end_date],
            appointment_date__isnull=False,
            status__in=["pending", "checked_in", "in_progress"],
            appointment_start_time__isnull=False,
        )
        if doctor_id:
            occupied_slots_qs = occupied_slots_qs.filter(doctor_id=doctor_id)
        for doc_id, appointment_date, appointment_start_time in occupied_slots_qs.values_list(
            "doctor_id",
            "appointment_date",
            "appointment_start_time",
        ):
            if not doc_id or not appointment_date or not appointment_start_time:
                continue
            occupied_slots_map[(doc_id, appointment_date)].add(
                appointment_start_time.strftime("%H:%M")
            )
        appt_qs = Appointment.objects.filter(
            appointment_date__range=[start_date, end_date],
            appointment_date__isnull=False
        )
        if doctor_id:
            appt_qs = appt_qs.filter(doctor_id=doctor_id)
        pending_qs = (
            appt_qs
            .filter(status="pending")
            .annotate(day=TruncDate('appointment_date'))
            .values('day')
            .annotate(count=Count('id'))
        )
        done_qs = (
            appt_qs
            .filter(status="done")
            .annotate(day=TruncDate('appointment_date'))
            .values('day')
            .annotate(count=Count('id'))
        )
        stats_map = {}
        for item in pending_qs:
            day = item['day'].isoformat()
            stats_map.setdefault(day, {
                "pending": 0,
                "done": 0
            })
            stats_map[day]["pending"] = item["count"]
        for item in done_qs:
            day = item['day'].isoformat()
            stats_map.setdefault(day, {
                "pending": 0,
                "done": 0
            })
            stats_map[day]["done"] = item["count"]
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        result_by_date = []
        for target_date in date_range:
            date_key = target_date.isoformat()
            day_stats = stats_map.get(date_key, {
                "pending": 0,
                "done": 0
            })
            day_item = {
                "date": str(target_date),
                "total_pending": day_stats["pending"],
                "total_done": day_stats["done"],
                "doctors": []
            }
            for doctor in doctors:
                model_weekday = (target_date.weekday() + 2) % 7
                schedule = doctor_schedule_map.get(doctor.id, {}).get(model_weekday)
                if not schedule:
                    continue
                exception = doctor_exception_map.get(doctor.id, {}).get(target_date)
                if exception and exception.is_available is False:
                    continue
                start_time = exception.start_time if exception and exception.start_time else schedule.start_time
                end_time = exception.end_time if exception and exception.end_time else schedule.end_time
                if not start_time or not end_time:
                    continue
                all_slots = generate_time_slots(start_time, end_time, schedule.slot_length or 20)
                if not all_slots:
                    continue
                occupied_str = occupied_slots_map.get((doctor.id, target_date), set())
                free_slots = [s for s in all_slots if s not in occupied_str]
                if free_slots:
                    day_item["doctors"].append({
                        "doctor_id": doctor.id,
                        "doctor_name": str(doctor.base_user) if doctor.base_user else f"دکتر {doctor.id}",
                        "specialty": doctor.specialty or "نامشخص",
                        "total_free": len(free_slots)
                    })
            if day_item["doctors"]:
                result_by_date.append(day_item)
        return Response(result_by_date)


class NextAppointmentView(APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "احراز هویت انجام نشده است."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            patient_obj = Patient.objects.get(base_user=user)
        except Patient.DoesNotExist:
            return Response(
                {"detail": "پروفایل بیمار برای این کاربر یافت نشد."},
                status=status.HTTP_404_NOT_FOUND
            )
        appointments = patient_obj.patient_appointment.filter(
            is_pass=False,                 
            next_appointment_date__isnull=False    
        ).exclude(
            status="canceled"               
        ).order_by(
            "next_appointment_date",
            "next_appointment_time"
        )
        serializer = NextAppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
