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

from appointment.filters import DateFilter
from appointment.models import Appointment
from common.paginations import CustomLimitOffsetPagination
from medicals.models import MedicalServices, Category
from users.models import Doctor, Patient
from section.models import SectionRoom
from shift.models import WeeklySchedule
from .generator import generate_time_slots, remove_occupied_slots
from .serializers import (
    AppointmentSerializer,
    NextAppointmentSerializer, 
    PatientOwnAppointmentSerializer,
    AppointmentListSerializer, 
)
from .types import AppointmentType



class PatientOwnAppointmentListView(ListAPIView):
    serializer_class = PatientOwnAppointmentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Appointment.objects.all()
    pagination_class = CustomLimitOffsetPagination
    filterset_class = DateFilter
    filter_backends = [DjangoFilterBackend,OrderingFilter,]
    ordering_fields = ('_created_at', "appointment_date",)
    search_fields = (
                    'patient__user__full_name', 
                    "section__title",
                    "medical_service__title", 
                    "patient__user__mobile"
                )

    def get_queryset(self):
        patient = Patient.objects.get(user=self.request.user)
        queryset = Appointment.objects.filter(patient=patient)
        start_date_from = self.request.query_params.get("start_date_from")
        if start_date_from:
            queryset = queryset.filter(appointment_date__gte=start_date_from)
        end_date_to = self.request.query_params.get("end_date_to")
        if end_date_to:
            queryset = queryset.filter(appointment_date__lte=end_date_to)
        return queryset.select_related(
            "patient",
            "doctor",
            "medical_service",
            "doctor__base_user",
        ).order_by("-appointment_date", "-time", "_created_at")


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentListSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_class = DateFilter
    ordering_fields = ('_created_at', "appointment_date",)
    search_fields = ('doctor__base_user__full_name', 
                    'patient__user__full_name', "section__title",
                    "medical_service__title", "patient__base_user__mobile"
                    )
    
    def get_queryset(self):
        return Appointment.objects.all().distinct()


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


class AllAvailableAppointmentsAPIView(APIView):
    def get(self, request):
        date_str = request.query_params.get("date")
        doctor_id = request.query_params.get("doctor_id")

        if not date_str:
            return Response({"detail": "پارامتر date الزامی است"}, status=400)
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "فرمت تاریخ اشتباه است (YYYY-MM-DD)"}, status=400)
        model_weekday = (target_date.weekday() + 2) % 7
        schedules = WeeklySchedule.objects.filter(
            weekday=model_weekday,
            doctor__isnull=False
        ).select_related('doctor', 'doctor__staff')
        if doctor_id:
            schedules = schedules.filter(doctor_id=doctor_id)
        if not schedules.exists():
            return Response([])
        result = []
        for schedule in schedules:
            doctor = schedule.doctor
            if not doctor:
                continue
            doctor_name = str(doctor.base_user) if doctor.base_user else f"دکتر (ID: {doctor.id})"
            exception = doctor.exceptions.filter(date=target_date).first()
            if exception and exception.is_available is False:
                continue
            start_time = (exception.start_time if exception and exception.start_time else schedule.start_time)
            end_time = (exception.end_time if exception and exception.end_time else schedule.end_time)
            if not start_time or not end_time:
                continue
            all_slots = generate_time_slots(start_time, end_time, schedule.slot_length or 20)
            if not all_slots:
                continue

            occupied_times = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=target_date,
                status__in=["pending", "checked_in", "in_progress"]
            ).values_list('appointment_start_time', flat=True)
            occupied_str = {t.strftime("%H:%M") for t in occupied_times if t}
            free_slots = [slot for slot in all_slots if slot not in occupied_str]

            if not free_slots:
                continue
            result.append({
                "doctor_id": doctor.id,
                "doctor_name": doctor_name,
                "date": str(target_date),
                "weekday_persian": schedule.get_weekday_display(),
                "shift": f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                "slot_duration_minutes": schedule.slot_length or 20,
                "available_slots": free_slots,
                "total_slots": len(all_slots),
                "booked_slots": len(all_slots) - len(free_slots),
            })

        result.sort(key=lambda x: x["doctor_name"])

        return Response(result)


class DoctorAvailableAppointmentsAPIView(APIView):
    def get(self, request):
        date_str = request.query_params.get("date")
        doctor_id = request.query_params.get("doctor_id")

        if not date_str or not doctor_id:
            return Response({"detail": "date and doctor_id required"}, status=400)
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        doctor = Doctor.objects.get(id=doctor_id)
        weekday = date.weekday()
        schedule = WeeklySchedule.objects.filter(
            doctor=doctor, weekday=weekday
        ).first()
        if not schedule:
            return Response({"slots": []})
        exc = doctor.exceptions.filter(date=date).first()
        if exc:
            if exc.is_available is False:
                return Response({"slots": []})
            start = exc.start_time
            end = exc.end_time
        else:
            start = schedule.start_time
            end = schedule.end_time
        slots = generate_time_slots(start, end, schedule.slot_length)
        free_slots = remove_occupied_slots(slots, doctor, date)
        return Response({
            "doctor_id": doctor.id,
            "doctor": str(doctor),
            "slots": free_slots
        })


class DoctorFreeSlotsAPIView(APIView):
    
    def get(self, request, doctor_id):
        date_str = request.query_params.get("date")
        if not date_str:
            return Response({"detail": "date required"}, status=400)
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        doctor = Doctor.objects.get(id=doctor_id)
        weekday = date.weekday()
        schedule = WeeklySchedule.objects.filter(
            doctor=doctor, weekday=weekday
        ).first()
        if not schedule:
            return Response({"slots": []})
        exc = doctor.exceptions.filter(date=date).first()
        if exc:
            if not exc.is_available:
                return Response({"slots": []})
            start = exc.start_time
            end = exc.end_time
        else:
            start = schedule.start_time
            end = schedule.end_time
        slots = generate_time_slots(start, end, schedule.slot_length)
        free_slots = remove_occupied_slots(slots, doctor, date)
        return Response({"slots": free_slots})


class AppointmentCreateAPIView(generics.CreateAPIView):
    serializer_class = AppointmentSerializer
    SLOT_MINUTES = 20

    def _get_instance(self, model, obj_id, title):
        if not obj_id:
            raise ValidationError({"detail": f"{title} الزامی است"})
        try:
            return model.objects.get(id=obj_id)
        except model.DoesNotExist:
            raise ValidationError({"detail": f"{title} یافت نشد"})

    def _parse_datetime(self, date_str, time_str):
        if not date_str:
                return None, None
        if not time_str:
            return datetime.strptime(date_str, "%Y-%m-%d").date(), None
        try:
            return (
                datetime.strptime(date_str, "%Y-%m-%d").date(),
                datetime.strptime(time_str, "%H:%M").time(),
            )
        except ValueError:
            raise ValidationError({"detail": "فرمت تاریخ یا زمان اشتباه است"})

    def _try_parse_optional_datetime(self, date_str, time_str):
        try:
            return self._parse_datetime(date_str, time_str)
        except:
            return None, None

    def _validate_doctor_schedule(self, doctor, date, start, end):
        weekday = (date.weekday() + 2) % 7
        schedule = WeeklySchedule.objects.filter(
            Q(doctor=doctor) | Q(staff=doctor.staff),
            weekday=weekday
        ).first()
        
        if not schedule:
            raise ValidationError({"detail": "پزشک در این روز شیفت ندارد"})
        exception = doctor.exceptions.filter(date=date).first()
        if exception and not exception.is_available:
            raise ValidationError({"detail": "پزشک در این روز تعطیل است"})
        shift_start = exception.start_time if exception and exception.start_time else schedule.start_time
        shift_end = exception.end_time if exception and exception.end_time else schedule.end_time

        if shift_start and start < shift_start:
            raise ValidationError({"detail": "زمان شروع قبل از شیفت است"})
        if shift_end and end > shift_end:
            raise ValidationError({"detail": "زمان پایان بعد از شیفت است"})

        slots = generate_time_slots(start, end, self.SLOT_MINUTES)
        occupied = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            appointment_start_time__lt=datetime.combine(date, end),
            appointment_end_time__gt=datetime.combine(date, start),
        ).exists()
        if occupied:
            raise ValidationError({"detail": "این زمان قبلاً رزرو شده است"})

    def _build_time_range_from_slots(self, date, slots):
        if not slots:
            raise ValidationError({"detail": "حداقل یک اسلات باید انتخاب شود"})
        slots = sorted(slots)
        start_time = datetime.strptime(slots[0], "%H:%M").time()
        last_slot_time = datetime.strptime(slots[-1], "%H:%M")
        end_time = (
            datetime.combine(date, last_slot_time.time()) +
            timedelta(minutes=self.SLOT_MINUTES)
        ).time()
        total_duration = len(slots) * self.SLOT_MINUTES
        return start_time, end_time, total_duration


    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        for field in ("date", "appointment_date", "appointment_start_time", "appointment_end_time"):
            if data.get(field) == "":
                data[field] = None

        requested_is_fixed = _normalize_optional_bool(data.get("is_fixed"))
                
        appointment_type = data.get("type", AppointmentType.visit)
        if appointment_type not in AppointmentType.values:
            return Response({"detail": "نوع نوبت نامعتبر است"}, status=400)
        doctor = self._get_instance(Doctor, data.get("doctor"), "پزشک")
        patient = self._get_instance(Patient, data.get("patient"), "بیمار")
        section = self._get_instance(SectionRoom, data.get("section"), "بخش") if data.get("section") else None
        category = self._get_instance(Category, data.get("category"), "سرفصل") if data.get("category") else None
        appointment_date = appointment_start_time = appointment_end_time = total_duration = None

        if appointment_type == AppointmentType.visit:
            appointment_date, appointment_start_time = self._parse_datetime(
                data.get("appointment_date"),
                data.get("appointment_start_time")
            )
            services = MedicalServices.objects.filter(id__in=data.get("services", []))
            blocks = sum(getattr(s, "blocks", 1) for s in services) or 1
            total_duration = blocks * self.SLOT_MINUTES
            if appointment_date and appointment_start_time:
                appointment_end_time = (
                    datetime.combine(appointment_date, appointment_start_time)
                    + timedelta(minutes=total_duration)
                ).time()
    
                self._validate_doctor_schedule(
                    doctor,
                    appointment_date,
                    appointment_start_time,
                    appointment_end_time
                )
            else:
                appointment_end_time = None
                total_duration = 0
        
        if appointment_type == AppointmentType.services:
            appointment_date, _ = self._parse_datetime(
                data.get("appointment_date"),
                None
            )
            slots = [s for s in data.get("slots", []) if s] 
            if appointment_date and slots:
                appointment_start_time, appointment_end_time, total_duration = (
                    self._build_time_range_from_slots(appointment_date, slots)
                )
                self._validate_doctor_schedule(
                    doctor,
                    appointment_date,
                    appointment_start_time,
                    appointment_end_time
                )
            else:
                appointment_start_time = appointment_end_time = None
                total_duration = 0

        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            type=appointment_type,
            appointment_date=appointment_date,
            appointment_start_time=appointment_start_time,
            appointment_end_time=appointment_end_time,
            total_duration=total_duration,
            status=status,
            number=data.get("number"),
            medical_service_id=data.get("medical_service"),
            category=category,
            date=data.get("date"),
            time=data.get("time"),
            section=section,
        )

        if appointment.custom_status and appointment.custom_status.status == "done":
            return Response({
                "success": True,
                "appointment_id": appointment.id,
                "type": appointment.type,
                "status": appointment.status,
                "appointment_date": appointment.appointment_date,
                "appointment_start_time": appointment.appointment_start_time,
                "appointment_end_time": appointment.appointment_end_time,
            }, status=201)


class AppointmentUpdateAPIView(generics.UpdateAPIView):
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
    lookup_field = 'pk' 

    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        was_fixed = appointment.is_fixed
        data = request.data.copy()
        appointment_type = data.get("type", appointment.type).lower()
        doctor_id = data.get("doctor", appointment.doctor.id)
        patient_id = data.get("patient", appointment.patient.id)
        medical_service_id = data.get("medical_service") or (appointment.medical_service.id if appointment.medical_service else None)
        if medical_service_id:
            appointment.medical_service = MedicalServices.objects.get(id=medical_service_id)
        if appointment_type == "visit":
            appointment_date_str = data.get("appointment_date") or str(appointment.appointment_date)
            appointment_start_str = data.get("appointment_start_time") or appointment.appointment_start_time.strftime("%H:%M")
            try:
                appointment_date = datetime.strptime(appointment_date_str, "%Y-%m-%d").date()
                appointment_start_time = datetime.strptime(appointment_start_str, "%H:%M").time()
            except ValueError:
                return Response({"detail": "فرمت appointment_date یا appointment_start_time اشتباه است"}, status=400)
            services = MedicalServices.objects.filter(id__in=medical_service_id)
            total_blocks = sum(getattr(s, 'blocks', 1) for s in services) or 1
            total_duration = total_blocks * 20
            appointment_end_dt = datetime.combine(appointment_date, appointment_start_time) + timedelta(minutes=total_duration)
            appointment_end_time = appointment_end_dt.time()

        elif appointment_type == "services":
            appointment_date = None
            appointment_start_time = None
            appointment_end_time = None
            total_duration = None
            if data.get("date") and data.get("time"):
                try:
                    appointment_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
                    appointment_start_time = datetime.strptime(data["time"], "%H:%M").time()
                except:
                    pass
        else:
            return Response({"detail": "نوع نوبت نامعتبر است (visit یا services)"}, status=400)
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            patient = Patient.objects.get(id=patient_id)
        except Doctor.DoesNotExist:
            return Response({"detail": "پزشک یافت نشد"}, status=404)
        except Patient.DoesNotExist:
            return Response({"detail": "بیمار یافت نشد"}, status=404)
        if appointment_type == "visit":
            python_weekday = appointment_date.weekday()
            model_weekday = (python_weekday + 2) % 7
            schedule = WeeklySchedule.objects.filter(
                Q(doctor=doctor) | Q(staff=doctor.staff),
                weekday=model_weekday
            ).first()

            if not schedule:
                return Response({"detail": "پزشک در این روز شیفت ندارد"}, status=400)
            exception = doctor.exceptions.filter(date=appointment_date).first()
            shift_start = exception.start_time if exception and exception.start_time else schedule.start_time
            shift_end = exception.end_time if exception and exception.end_time else schedule.end_time
            
            if shift_start and appointment_start_time < shift_start:
                return Response({"detail": "زمان شروع قبل از شیفت است"}, status=400)
            
            if shift_end and appointment_end_time > shift_end:
                return Response({"detail": "زمان پایان بعد از شیفت است"}, status=400)
            needed_slots = generate_time_slots(appointment_start_time, appointment_end_time, 20)
            occupied = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_start_time__in=[datetime.combine(appointment_date, datetime.strptime(s, "%H:%M").time()) for s in needed_slots]
            ).exclude(id=appointment.id).exists()
            if occupied:
                return Response({"detail": "این زمان قبلاً رزرو شده است"}, status=400)

        appointment.doctor = doctor
        appointment.patient = patient
        appointment.type = appointment_type.upper()
        appointment.appointment_date = appointment_date
        appointment.appointment_start_time = appointment_start_time
        appointment.appointment_end_time = appointment_end_time
        appointment.total_duration = total_duration
        appointment.status = "pending" if appointment_type == "visit" else "pending"
        appointment.date = data.get("date", appointment.date)
        appointment.time = data.get("time", appointment.time)
        if "is_fixed" in data:
            appointment.is_fixed = _normalize_optional_bool(data.get("is_fixed"))
        appointment.save()

        if medical_service_id:
            appointment.medical_service = MedicalServices.objects.get(id=medical_service_id)
            appointment.save()

        return Response({
            "success": True,
            "message": "نوبت با موفقیت بروزرسانی شد",
            "appointment_id": appointment.id,
            "type": appointment_type,
            "status": appointment.status,
            "appointment_time": appointment_start_time.strftime("%H:%M") if appointment_start_time else None,
            "appointment_date": str(appointment_date) if appointment_date else None,
        }, status=200)


class AppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentListSerializer
    queryset = Appointment.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = (
        'patient__base_user__first_name',
        'patient__base_user__last_name',
        'patient__base_user__mobile',
        'doctor__base_user__first_name',
        'doctor__base_user__last_name',
    )
    ordering_fields = (
        'date',
        'patient__base_user__first_name',
        'doctor__base_user__first_name',
    )
    ordering = ('date',)



class PatientAppointmentListAPIView(APIView):

    def get(self, request):
        date_str = request.query_params.get("date")
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        if date_str:
            try:
                start_date = end_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"detail": "فرمت date اشتباه است"}, status=400)
        else:
            if not start_date_str or not end_date_str:
                return Response({"detail": "date یا start_date/end_date الزامی است"}, status=400)
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"detail": "فرمت تاریخ اشتباه است"}, status=400)
        if start_date > end_date:
            return Response({"detail": "start_date نمی‌تواند بعد از end_date باشد"}, status=400)
        queryset = Appointment.objects.filter(
            appointment_date__range=[start_date, end_date],
            appointment_date__isnull=False
        ).select_related(
            'doctor', 'doctor__staff', 'patient', 'patient__user',
        ).prefetch_related('medical_service')

        doctor_id = request.query_params.get("doctor_id")
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)

        section_id = request.query_params.get("section_id")
        if section_id:
            queryset = queryset.filter(section_id=section_id)

        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)


        if not queryset.exists():
            return Response([])

        doctor_dict = {}

        for appt in queryset.order_by('appointment_date', 'appointment_start_time'):
            doctor = appt.doctor
            if not doctor:
                continue

            doctor_key = str(doctor.id)
            if doctor_key not in doctor_dict:
                doctor_dict[doctor_key] = {
                    "doctor_id": doctor_key,
                    "doctor_name": str(doctor.staff) if doctor.staff else "نامشخص",
                    "specialty": doctor.specialty or "نامشخص",
                    "appointments": []
                }

            patient_user = appt.patient.user if appt.patient and hasattr(appt.patient, 'user') else None

            doctor_dict[doctor_key]["appointments"].append({
                "id": str(appt.id),
                "type": appt.type.lower() if appt.type else "visit",
                "title": appt.title or ("ویزیت" if appt.type == "visit" else "خدمات"),
                "patient": {
                    "id": str(appt.patient.id) if appt.patient else None,
                    "user": {
                        "id": str(patient_user.id) if patient_user else None,
                        "first_name": patient_user.first_name if patient_user else "",
                        "last_name": patient_user.last_name if patient_user else "",
                        "mobile": patient_user.mobile if patient_user else "",
                    } if patient_user else None
                },
                "section_title": appt.section.title if appt.section else "نامشخص",
                "appointment_date": str(appt.appointment_date),
                "appointment_start_time": appt.appointment_start_time.strftime("%H:%M") if appt.appointment_start_time else None,
                "appointment_end_time": appt.appointment_end_time.strftime("%H:%M") if appt.appointment_end_time else None,
                "status": appt.status,
                "medical_service": appt.medical_service.title if appt.medical_service else "نامشخص",
            })
        result = list(doctor_dict.values())
        result.sort(key=lambda x: x["doctor_name"])
        return Response(result)


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


class DoctorDayOverviewAPIView(APIView):
    
    def get(self, request):
        date_str = request.query_params.get("date")
        doctor_id = request.query_params.get("doctor_id")
        if not date_str:
            return Response({"detail": "date required"}, status=400)
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        weekday = (target_date.weekday() + 2) % 7
        schedules = WeeklySchedule.objects.filter(
            weekday=weekday,
            active=True,
            doctor__isnull=False
        ).select_related("doctor", "doctor__staff")
        if doctor_id:
            schedules = schedules.filter(doctor_id=doctor_id)
        if not schedules.exists():
            return Response([])
        doctor_ids = [s.doctor_id for s in schedules]
        appointments = Appointment.objects.filter(
            appointment_date=target_date,
            doctor_id__in=doctor_ids
        ).select_related(
            "doctor", "supervisor", "assist", "patient",
            "medical_service", "category", "section"
        )
        appointment_map = {}
        for a in appointments:
            did = str(a.doctor_id)
            appointment_map.setdefault(did, []).append({
                "appointment_id": a.id,
                "title": a.title,
                "number": a.number,
                "status": a.status,
                "type": a.type,
                "is_fixed": a.is_fixed,
                "is_pass": a.is_pass,
                "appointment_date": a.appointment_date.strftime("%Y-%m-%d") if a.appointment_date else None,
                "appointment_start_time": a.appointment_start_time.strftime("%H:%M") if a.appointment_start_time else None,
                "appointment_end_time": a.appointment_end_time.strftime("%H:%M") if a.appointment_end_time else None,
            })

        result = []
        for s in schedules:
            doctor = s.doctor
            did = str(doctor.id)
            result.append({
                "doctor_id": doctor.id,
                "doctor_name": str(doctor.staff) if doctor.staff else f"دکتر (ID:{doctor.id})",
                "date": str(target_date),
                "weekday": s.get_weekday_display(),
                "shift": f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}",
                "appointments": appointment_map.get(did, [])
            })
        return Response(result)
