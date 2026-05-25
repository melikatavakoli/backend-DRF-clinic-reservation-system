from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from shift.models import ExceptionDate, WeeklySchedule
from shift.serializers import ( ExceptionDateSerializer, WeeklyScheduleSerializer )
from users.models import Doctor


class WeeklyScheduleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WeeklyScheduleSerializer
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'doctor_profile'):
            return WeeklySchedule.objects.filter(doctor=user.doctor_profile)
        return WeeklySchedule.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'doctor_profile'):
            serializer.save(doctor=user.doctor_profile)


class ExceptionDateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ExceptionDateSerializer
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'doctor_profile'):
            return ExceptionDate.objects.filter(doctor=user.doctor_profile)
        return ExceptionDate.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'doctor_profile'):
            serializer.save(doctor=user.doctor_profile)
    
    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming_exceptions(self, request):
        """دریافت روزهای استثنای آینده"""
        exceptions = self.get_queryset().filter(
            date__gte=timezone.now().date()
        ).order_by('date')
        return Response(ExceptionDateSerializer(exceptions, many=True).data)


class DoctorScheduleViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='doctor/(?P<doctor_id>[^/.]+)')
    def get_doctor_schedule(self, request, doctor_id=None):
        doctor = Doctor.objects.filter(id=doctor_id).first()
        if not doctor:
            return Response({"error": "پزشک یافت نشد"}, status=404)
        weekly_schedule = WeeklySchedule.objects.filter(doctor=doctor, active=True)
        exceptions = ExceptionDate.objects.filter(doctor=doctor)
        data = {
            'doctor_id': doctor.id,
            'doctor_name': doctor.get_full_name(),
            'weekly_schedule': WeeklyScheduleSerializer(weekly_schedule, many=True).data,
            'exceptions': ExceptionDateSerializer(exceptions, many=True).data
        }
        return Response(data)