from rest_framework import serializers

from shift.models import WeeklySchedule, ExceptionDate
from users.models import Doctor


class WeeklyScheduleSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.select_related("user__base_user"),
        required=False,
    )

    class Meta:
        model = WeeklySchedule
        fields = [
            "id",
            "active",
            "doctor",
            "weekday",
            "start_time",
            "end_time",
            "slot_length",
        ]


class DoctorExceptionDateSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.select_related("user__base_user")
    )

    class Meta:
        model = ExceptionDate
        fields = [
            "id",
            "doctor",
            "date",
            "is_available",
            "start_time",
            "end_time",
        ]
