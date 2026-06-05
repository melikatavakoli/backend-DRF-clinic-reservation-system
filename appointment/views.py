from datetime import datetime, timedelta
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404

from appointment.models import Appointment, AppointmentReminder
from users.models import Doctor, Patient
from shift.models import ExceptionDate, WeeklySchedule
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentStatusUpdateSerializer,
    AppointmentUpdateSerializer,
    NextAppointmentSerializer,
    AppointmentListSerializer,
)
from .types import AppointmentStatus


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.all()

        if user.is_staff or user.is_superuser:
            queryset = queryset.all()
        elif hasattr(user, "doctor_profile") and user.doctor_profile:
            queryset = queryset.filter(doctor=user.doctor_profile)
        elif hasattr(user, "patient_profile") and user.patient_profile:
            queryset = queryset.filter(patient=user.patient_profile)
        elif hasattr(user, "receptionist_profile"):
            queryset = queryset.all()
        else:
            queryset = queryset.filter(
                Q(patient__base_user=user) | Q(doctor__base_user=user)
            )

        query_params = self.request.query_params

        if query_params.get("patient_id"):
            queryset = queryset.filter(patient_id=query_params["patient_id"])
        if query_params.get("doctor_id"):
            queryset = queryset.filter(doctor_id=query_params["doctor_id"])
        if query_params.get("status"):
            queryset = queryset.filter(status=query_params["status"])
        if query_params.get("type"):
            queryset = queryset.filter(type=query_params["type"])
        if query_params.get("date_from"):
            queryset = queryset.filter(appointment_date__gte=query_params["date_from"])
        if query_params.get("date_to"):
            queryset = queryset.filter(appointment_date__lte=query_params["date_to"])
        if query_params.get("is_paid") is not None:
            is_paid = query_params["is_paid"].lower() == "true"
            queryset = queryset.filter(is_paid=is_paid)
        if query_params.get("is_urgent") is not None:
            is_urgent = query_params["is_urgent"].lower() == "true"
            queryset = queryset.filter(is_urgent=is_urgent)

        return queryset.select_related(
            "patient", "doctor", "medical_service", "section"
        ).prefetch_related("blocks", "reminders")

    def get_serializer_class(self):
        if self.action == "list":
            return AppointmentListSerializer
        elif self.action == "create":
            return AppointmentCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return AppointmentUpdateSerializer
        elif self.action == "retrieve":
            return AppointmentDetailSerializer
        return AppointmentDetailSerializer

    @action(detail=False, methods=["get"], url_path="my-appointments")
    def my_appointments(self, request):
        """دریافت نوبت‌های کاربر جاری"""
        user = request.user
        if user.is_staff or user.is_superuser:
            appointments = Appointment.objects.all()
        elif hasattr(user, "patient_profile"):
            appointments = Appointment.objects.filter(patient=user.patient_profile)
        elif hasattr(user, "doctor_profile"):
            appointments = Appointment.objects.filter(doctor=user.doctor_profile)
        else:
            return Response({"error": "شما دسترسی به این بخش ندارید"}, status=403)
        today = timezone.now().date()
        upcoming = appointments.filter(
            appointment_date__gte=today,
            status__in=[
                AppointmentStatus.pending,
                AppointmentStatus.in_progress,
            ],
        )
        past = appointments.filter(
            Q(appointment_date__lt=today) | Q(status=AppointmentStatus.done)
        )
        return Response(
            {
                "upcoming": AppointmentListSerializer(upcoming, many=True).data,
                "past": AppointmentListSerializer(past, many=True).data,
                "total": appointments.count(),
            }
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="available-slots/(?P<doctor_id>[^/.]+)",
    )
    def available_slots(self, request, doctor_id=None):
        """دریافت زمان‌های خالی پزشک"""
        date_str = request.query_params.get("date")

        if not date_str:
            return Response(
                {"error": "پارامتر date الزامی است"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "فرمت تاریخ باید YYYY-MM-DD باشد"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doctor = get_object_or_404(Doctor, id=doctor_id)

        weekday = date.weekday()

        weekly_schedule = WeeklySchedule.objects.filter(
            doctor=doctor, weekday=weekday, active=True
        ).first()

        if not weekly_schedule:
            return Response({"message": "پزشک در این روز کاری ندارد", "slots": []})

        booked_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            status__in=[
                AppointmentStatus.pending,
                AppointmentStatus.done,
                AppointmentStatus.in_progress,
            ],
        ).values_list("appointment_start_time", flat=True)

        exception = ExceptionDate.objects.filter(doctor=doctor, date=date).first()

        if exception and not exception.is_available:
            return Response({"message": "پزشک در این تاریخ مرخصی دارد", "slots": []})

        start_time = (
            exception.start_time
            if exception and exception.start_time
            else weekly_schedule.start_time
        )
        end_time = (
            exception.end_time
            if exception and exception.end_time
            else weekly_schedule.end_time
        )
        slot_length = weekly_schedule.slot_length or 20

        from datetime import datetime

        available_slots = []
        current_time = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)

        while current_time + timedelta(minutes=slot_length) <= end_datetime:
            slot_start = current_time.time()
            slot_end = (current_time + timedelta(minutes=slot_length)).time()

            if slot_start not in booked_appointments:
                available_slots.append(
                    {
                        "start_time": slot_start.strftime("%H:%M"),
                        "end_time": slot_end.strftime("%H:%M"),
                        "is_available": True,
                    }
                )

            current_time += timedelta(minutes=slot_length)

        return Response(
            {
                "doctor_id": doctor.id,
                "doctor_name": doctor.get_full_name(),
                "date": date_str,
                "day_of_week": weekday,
                "working_hours": {
                    "start": (start_time.strftime("%H:%M") if start_time else None),
                    "end": end_time.strftime("%H:%M") if end_time else None,
                },
                "slot_length": slot_length,
                "total_slots": len(available_slots),
                "slots": available_slots,
            }
        )

    @action(detail=False, methods=["post"], url_path="book")
    def book_appointment(self, request):
        """رزرو نوبت جدید توسط بیمار"""
        if not (
            hasattr(request.user, "patient_profile")
            or request.user.is_staff
            or request.user.is_superuser
        ):
            return Response(
                {"error": "فقط بیماران می‌توانند نوبت رزرو کنند"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = AppointmentCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save(patient=request.user.patient_profile)
        if appointment.final_amount > 0:
            return Response(
                {
                    "appointment": AppointmentDetailSerializer(appointment).data,
                    "message": "لطفاً برای تکمیل نوبت، پرداخت را انجام دهید",
                },
                status=status.HTTP_201_CREATED,
            )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_appointment(self, request, pk=None):
        """لغو نوبت"""
        appointment = self.get_object()
        user = request.user
        has_access = (
            user.is_staff
            or user.is_superuser
            or (
                hasattr(user, "patient_profile")
                and appointment.patient == user.patient_profile
            )
            or (
                hasattr(user, "doctor_profile")
                and appointment.doctor == user.doctor_profile
            )
            or hasattr(user, "receptionist_profile")
        )
        if not has_access:
            return Response(
                {"error": "شما دسترسی لغو این نوبت را ندارید"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not appointment.is_upcoming():
            return Response(
                {"error": "امکان لغو این نوبت وجود ندارد"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AppointmentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment.cancel(reason=serializer.validated_data.get("cancellation_reason"))
        return Response(
            {
                "message": "نوبت با موفقیت لغو شد",
                "appointment": AppointmentDetailSerializer(appointment).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="reschedule")
    def reschedule_appointment(self, request, pk=None):
        """تغییر زمان نوبت"""
        appointment = self.get_object()
        new_date = request.data.get("appointment_date")
        new_time = request.data.get("appointment_start_time")
        if not new_date or not new_time:
            return Response(
                {"error": "لطفاً تاریخ و زمان جدید را وارد کنید"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        overlapping = Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=new_date,
            appointment_start_time=new_time,
            status__in=[AppointmentStatus.pending, AppointmentStatus.done],
        ).exclude(id=appointment.id)
        if overlapping.exists():
            return Response(
                {"error": "زمان انتخابی قبلاً رزرو شده است"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.appointment_date = new_date
        appointment.appointment_start_time = new_time
        appointment.status = AppointmentStatus.moved
        appointment.save()
        appointment.blocks.all().delete()
        return Response(
            {
                "message": "زمان نوبت با موفقیت تغییر کرد",
                "appointment": AppointmentDetailSerializer(appointment).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request, pk=None):
        """ثبت مراجعه بیمار (برای منشی/پزشک)"""
        appointment = self.get_object()
        if appointment.status != AppointmentStatus.done:
            return Response(
                {"error": "فقط نوبت‌های تایید شده قابلیت مراجعه دارند"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.check_in()
        return Response(
            {
                "message": "مراجعه بیمار ثبت شد",
                "appointment": AppointmentDetailSerializer(appointment).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="start-visit")
    def start_visit(self, request, pk=None):
        """شروع ویزیت (برای پزشک)"""
        appointment = self.get_object()
        if (
            not hasattr(request.user, "doctor_profile")
            or appointment.doctor != request.user.doctor_profile
        ):
            return Response(
                {"error": "فقط پزشک مربوطه می‌تواند ویزیت را شروع کند"},
                status=status.HTTP_403_FORBIDDEN,
            )
        appointment.start_visit()
        return Response(
            {
                "message": "ویزیت شروع شد",
                "appointment": AppointmentDetailSerializer(appointment).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="complete")
    def complete_appointment(self, request, pk=None):
        """اتمام ویزیت"""
        appointment = self.get_object()
        appointment.complete()
        return Response(
            {
                "message": "ویزیت به پایان رسید",
                "appointment": AppointmentDetailSerializer(appointment).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="send-reminder")
    def send_reminder(self, request, pk=None):
        """ارسال یادآوری برای بیمار"""
        appointment = self.get_object()
        reminder_type = request.data.get("reminder_type", "sms")
        AppointmentReminder.objects.create(
            appointment=appointment,
            reminder_type=reminder_type,
            status="sent",
        )
        appointment.reminder_sent = True
        appointment.save()
        return Response({"message": f"یادآوری از طریق {reminder_type} ارسال شد"})


class NextAppointmentView(APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "احراز هویت انجام نشده است."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.is_staff or user.is_superuser:
            appointments = (
                Appointment.objects.filter(
                    is_pass=False, next_appointment_date__isnull=False
                )
                .exclude(status="canceled")
                .order_by("next_appointment_date", "next_appointment_time")
            )
            serializer = NextAppointmentSerializer(appointments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        try:
            patient_obj = Patient.objects.get(base_user=user)
        except Patient.DoesNotExist:
            return Response(
                {"detail": "پروفایل بیمار برای این کاربر یافت نشد."},
                status=status.HTTP_404_NOT_FOUND,
            )
        appointments = (
            patient_obj.patient_appointment.filter(
                is_pass=False, next_appointment_date__isnull=False
            )
            .exclude(status="canceled")
            .order_by("next_appointment_date", "next_appointment_time")
        )
        serializer = NextAppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
