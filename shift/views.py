from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from common.views import BaseModelViewSet
from shift.models import ExceptionDate, WeeklySchedule
from shift.serializers import (
    ExceptionDateSerializer,
    WeeklyScheduleSerializer,
)
from users.models import Doctor


class WeeklyScheduleViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WeeklyScheduleSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return WeeklySchedule.objects.all()
        if hasattr(user, "doctor_profile"):
            return WeeklySchedule.objects.filter(doctor=user.doctor_profile)
        return WeeklySchedule.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        doctor = None
        if hasattr(user, "doctor_profile"):
            doctor = user.doctor_profile
        elif user.is_staff and "doctor" in self.request.data:
            doctor_id = self.request.data["doctor"]
            doctor = Doctor.objects.get(id=doctor_id)
        else:
            raise PermissionError("فقط پزشکان می‌توانند شیفت ثبت کنند")
        super().perform_create(serializer)
        serializer.instance.doctor = doctor
        serializer.instance.save()


class ExceptionDateViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ExceptionDateSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return ExceptionDate.objects.all()
        if hasattr(user, "doctor_profile"):
            return ExceptionDate.objects.filter(doctor=user.doctor_profile)
        return ExceptionDate.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        doctor = None
        if hasattr(user, "doctor_profile"):
            doctor = user.doctor_profile
        elif user.is_staff and "doctor" in self.request.data:
            doctor_id = self.request.data["doctor"]
            doctor = Doctor.objects.get(id=doctor_id)
        else:
            raise PermissionError("فقط پزشکان می‌توانند تاریخ ثبت کنند")
        super().perform_create(serializer)
        serializer.instance.doctor = doctor
        serializer.instance.save()

    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming_exceptions(self, request):
        """دریافت روزهای استثنای آینده"""
        exceptions = (
            self.get_queryset().filter(date__gte=timezone.now().date()).order_by("date")
        )
        return Response(ExceptionDateSerializer(exceptions, many=True).data)


class DoctorScheduleViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="doctor/(?P<doctor_id>[^/.]+)")
    def get_doctor_schedule(self, request, doctor_id=None):
        doctor = Doctor.objects.filter(id=doctor_id).first()
        if not doctor:
            return Response({"error": "پزشک یافت نشد"}, status=404)
        weekly_schedule = WeeklySchedule.objects.filter(doctor=doctor, active=True)
        exceptions = ExceptionDate.objects.filter(doctor=doctor)
        data = {
            "doctor_id": doctor.id,
            "doctor_name": doctor.base_user.full_name,
            "weekly_schedule": WeeklyScheduleSerializer(
                weekly_schedule, many=True
            ).data,
            "exceptions": ExceptionDateSerializer(exceptions, many=True).data,
        }
        return Response(data)
