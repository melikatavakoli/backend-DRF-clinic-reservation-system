from appointment.types import AppointmentStatus, AppointmentType
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta

from appointment.models import (Appointment, AppointmentBlock, AppointmentReminder,)
from core.serializers import BaseUserSerializer
from medicals.serializers import MedicalServiceSerializer
from section.serializers import SectionRoomSerializer
from shift.models import ExceptionDate, WeeklySchedule
from users.models import Patient
from users.serializers import DoctorSerializer, PatientSerializer

User = get_user_model()


class AppointmentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentBlock
        fields = ['id', 'start_time', 'end_time', 'created_at', 'updated_at']
        

class AppointmentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentReminder
        fields = ['id', 'reminder_type', 'sent_at', 'status']
        

class AppointmentListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    doctor_specialty = serializers.CharField(source='doctor.specialty', read_only=True, allow_null=True)
    medical_service_name = serializers.CharField(source='medical_service.name', read_only=True, allow_null=True)
    section_name = serializers.CharField(source='section.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'title', 'patient_name', 'doctor_name',
            'doctor_specialty', 'medical_service_name', 'section_name',
            'appointment_date', 'appointment_start_time', 'appointment_end_time',
            'status', 'status_display', 'type', 'type_display', 'fee', 
            'final_amount', 'is_paid', 'is_urgent', 'is_pass',
        ]
        

class AppointmentDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    medical_service = MedicalServiceSerializer(read_only=True)
    section = SectionRoomSerializer(read_only=True)
    blocks = AppointmentBlockSerializer(many=True, read_only=True)
    reminders = AppointmentReminderSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['id', 'title', 'final_amount', 'created_at', 'updated_at']


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'medical_service', 'category', 'section',
            'appointment_date', 'appointment_start_time', 'duration_minutes',
            'type', 'symptoms', 'notes', 'is_urgent', 'fee', 'discount_amount'
        ]
    
    def validate(self, data):
        if not data.get('doctor'):
            raise serializers.ValidationError({"doctor": "انتخاب پزشک الزامی است"})

        appointment_date = data.get('appointment_date')
        appointment_time = data.get('appointment_start_time')
        
        if appointment_date < timezone.now().date():
            raise serializers.ValidationError({"appointment_date": "تاریخ انتخابی نمی‌تواند در گذشته باشد"})
        
        if appointment_date == timezone.now().date() and appointment_time < timezone.now().time():
            raise serializers.ValidationError({"appointment_start_time": "زمان انتخابی نمی‌تواند در گذشته باشد"})

        overlapping = Appointment.objects.filter(
            doctor=data['doctor'],
            appointment_date=appointment_date,
            appointment_start_time=appointment_time,
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED, AppointmentStatus.CHECKED_IN]
        )
        
        if overlapping.exists():
            raise serializers.ValidationError({"appointment_start_time": "این زمان قبلاً رزرو شده است"})

        weekday = appointment_date.weekday()
        weekly_schedule = WeeklySchedule.objects.filter(
            doctor=data['doctor'],
            weekday=weekday,
            active=True
        ).first()
        
        if not weekly_schedule:
            raise serializers.ValidationError({"doctor": "پزشک در این روز کاری ندارد"})

        if appointment_time < weekly_schedule.start_time or appointment_time > weekly_schedule.end_time:
            raise serializers.ValidationError({
                "appointment_start_time": f"زمان کاری پزشک از {weekly_schedule.start_time} تا {weekly_schedule.end_time} است"
            })

        exception = ExceptionDate.objects.filter(
            doctor=data['doctor'],
            date=appointment_date
        ).first()
        
        if exception and not exception.is_available:
            raise serializers.ValidationError({"doctor": "پزشک در این تاریخ مرخصی دارد"})
        
        return data
    
    def create(self, validated_data):
        with transaction.atomic():
            duration_minutes = validated_data.get('duration_minutes', 20)

            fee = validated_data.get('fee', 0)
            discount = validated_data.get('discount_amount', 0)
            final_amount = fee - discount

            appointment = Appointment.objects.create(
                **validated_data,
                final_amount=final_amount,
                status=AppointmentStatus.PENDING,
                total_duration=duration_minutes
            )

            self.create_appointment_blocks(appointment)
            
            return appointment
    
    def create_appointment_blocks(self, appointment):
        if appointment.appointment_start_time and appointment.total_duration:
            start = datetime.combine(appointment.appointment_date, appointment.appointment_start_time)
            interval = timedelta(minutes=appointment.total_duration // 4)  # تقسیم به 4 بخش
            
            for i in range(4):
                block_start = start + (i * interval)
                block_end = block_start + interval
                
                AppointmentBlock.objects.create(
                    appointment=appointment,
                    start_time=block_start.time(),
                    end_time=block_end.time()
                )


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'status', 'appointment_date', 'appointment_start_time',
            'notes', 'cancellation_reason', 'is_paid', 'discount_amount'
        ]
    
    def validate(self, data):
        if 'status' in data and data['status'] == AppointmentStatus.CANCELLED:
            if not data.get('cancellation_reason'):
                raise serializers.ValidationError({"cancellation_reason": "لطفاً دلیل لغو نوبت را وارد کنید"})
        return data
    
    
class AppointmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=AppointmentStatus.choices)
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        if value == AppointmentStatus.CANCELLED:
            if not self.initial_data.get('cancellation_reason'):
                raise serializers.ValidationError("برای لغو نوبت، دلیل لغو الزامی است")
        return value


class UserAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'role',
            'mobile',
        )


class PatientAppointmentSerializer(serializers.ModelSerializer):
    user = UserAppointmentSerializer()
    gender = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id",
            "user",
            "gender",
        )

    def get_gender(self, obj):
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        patient_info_items = prefetched.get("patient_info")
        if patient_info_items is not None:
            first_info = patient_info_items[0] if patient_info_items else None
            return getattr(first_info, "gender", None) if first_info else None
        first_info = obj.patient_info.order_by("id").first()
        return getattr(first_info, "gender", None) if first_info else None


class NextAppointmentSerializer(BaseUserSerializer):
    doctor_name = serializers.CharField(source="doctor.base_user.full_name", read_only=True)
    medical_service = MedicalServiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Appointment
        fields = BaseUserSerializer.Meta.fields +(
            "id",
            "doctor",
            'doctor_name',
            'medical_service',
            "next_appointment_date",
            "next_appointment_time",
            'is_fixed',
        )


class PatientOwnAppointmentSerializer(BaseUserSerializer):
    doctor_name = serializers.CharField(source="doctor.base_user.full_name", read_only=True)
    medical_service = serializers.CharField(source="medical_service.title", read_only=True)

    class Meta:
        model = Appointment
        fields = BaseUserSerializer.Meta.fields +(
            "id",
            "doctor",
            'medical_service',
            "appointment_date",
            "time",
            'doctor_name',
            "date",
            'medical_service',
            'is_fixed'
        )


class AvailableSlotSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField(required=True)
    date = serializers.DateField(required=True)
    service_id = serializers.IntegerField(required=False, allow_null=True)
    

class AvailableTimeSlotSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    is_available = serializers.BooleanField()
    

class AppointmentFilterSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=False)
    doctor_id = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=AppointmentStatus.choices, required=False)
    type = serializers.ChoiceField(choices=AppointmentType.choices, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    is_paid = serializers.BooleanField(required=False)
    is_urgent = serializers.BooleanField(required=False)