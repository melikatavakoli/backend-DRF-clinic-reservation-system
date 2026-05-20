from rest_framework import serializers
from django.contrib.auth import get_user_model

from appointment.models import (Appointment, AppointmentBlock,)
from core.serializers import BaseUserSerializer
from medicals.serializers import MedicalServiceSerializer
from medicals.models import MedicalServices
from users.models import Patient
from users.serializers import DoctorSerializer
from appointment.services import NullableDateField, NullableTimeField

User = get_user_model()


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


class AppointmentBlockSerializer(BaseUserSerializer):
    class Meta:
        model = AppointmentBlock
        fields = BaseUserSerializer.Meta.fields +(
            "id", 
            "start_time", 
            "end_time"
        )

    
class AppointmentSerializer(BaseUserSerializer):
    doctor = DoctorSerializer(read_only=True)
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all(), required=False)
    patient_details =PatientAppointmentSerializer(source="patient", read_only=True)
    appointment_date = NullableDateField(required=False, allow_null=True)
    date = NullableDateField(required=False, allow_null=True)
    appointment_start_time = NullableTimeField(required=False,allow_null=True)
    appointment_end_time = NullableTimeField(required=False,allow_null=True)

    class Meta:
        model = Appointment
        fields = BaseUserSerializer.Meta.fields +(
            "id",
            "doctor",
            "patient",
            "medical_service",
            "section",
            "type",
            'patient_details',
            "appointment_date",
            "appointment_start_time",
            "appointment_end_time",
            "date",
            "time",
            "next_appointment_time",
            "next_appointment_date",
            "total_duration",
            "status",
            "is_advise",
            'is_fixed',
        )
    extra_kwargs = {
        'appointment_date': {'required': False, 'allow_null': True},
        'date': {'required': False, 'allow_null': True},
    }

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        raw_is_fixed = attrs.get('is_fixed', instance.is_fixed if instance else False)
        def to_bool(val):
            if isinstance(val, bool):
                return val
            if val is None:
                return False
            if isinstance(val, str):
                return val.strip().lower() in ['true', '1', 'yes', 'y']
            return bool(val)
        is_fixed = to_bool(raw_is_fixed)
        if not is_fixed:
            start = attrs.get('appointment_start_time', None)
            end = attrs.get('appointment_end_time', None)
            if start == "":
                attrs['appointment_start_time'] = None
            if end == "":
                attrs['appointment_end_time'] = None
            if attrs.get('appointment_date', None) == "":
                attrs['appointment_date'] = None
            if attrs.get('date', None) == "":
                attrs['date'] = None
            final_date = attrs.get('date', getattr(instance, 'date', None))
            final_appointment_date = attrs.get(
                'appointment_date',
                getattr(instance, 'appointment_date', None)
            )
            if not final_date and not final_appointment_date:
                raise serializers.ValidationError({
                    "date": "Either date or appointment_date must be provided when is_fixed is False."
                })
        return super().validate(attrs)
    

class AppointmentListSerializer(BaseUserSerializer):
    doctor = DoctorSerializer(read_only=True)
    patient = PatientAppointmentSerializer(read_only=True)
    medical_service = serializers.PrimaryKeyRelatedField(queryset=MedicalServices.objects.all(),)
    medical_service_titles = serializers.CharField(source="medical_service.title", read_only=True)
    category_title = serializers.CharField(source="category.title", read_only=True)
    section_title = serializers.CharField(source="section.title", read_only=True)
    section_color = serializers.CharField(source="section.color", read_only=True)
    appointment_date = serializers.SerializerMethodField()
    appointment_start_time = serializers.SerializerMethodField()
    appointment_end_time = serializers.SerializerMethodField()
    enter_section_time = serializers.SerializerMethodField()
    date = serializers.DateField(format="%Y-%m-%d", required=True)
    
    class Meta:
        model = Appointment
        fields = BaseUserSerializer.Meta.fields +(
            "id",
            "title",
            "number",
            "doctor",
            "patient",
            "category",
            "medical_service",
            "section",
            "section_title",
            "section_color",
            "type",
            "appointment_date",
            "appointment_start_time",
            "appointment_end_time",
            "medical_service_titles",
            "category_title",
            "enter_section_time",
            "status",
            'is_pass',
            "is_advise",
            'is_fixed',
            'date'
        )

    def get_appointment_date(self, obj):
        if obj.appointment_date:
            return obj.appointment_date.strftime("%Y-%m-%d")
        return None
    
    def get_appointment_start_time(self, obj):
        if obj.appointment_start_time:
            return obj.appointment_start_time.strftime("%H:%M:%S")
        return None

    def get_appointment_end_time(self, obj):
        if obj.appointment_end_time:
            return obj.appointment_end_time.strftime("%H:%M:%S")
        return None

    def get_enter_section_time(self, obj):
        if obj.enter_section_time:
            return obj.enter_section_time.strftime("%H:%M:%S")
        elif obj.status == "persent" and obj.appointment_start_time:
            return obj.appointment_start_time.strftime("%H:%M:%S")
        return None
    
    
class AppointmentTVSerializer(BaseUserSerializer):
    section = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = BaseUserSerializer.Meta.fields +(
            "id",
            "type",
            "medical_service",
            "section",
            "status",
            'is_fixed',
        )

    def get_section(self, obj):
        if obj.section:
            return {
                "id": str(obj.section.id),
                "title": obj.section.title,
            }
        return None


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
