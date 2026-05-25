from rest_framework import serializers

from shift.models import WeeklySchedule, ExceptionDate


class WeeklyScheduleSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = WeeklySchedule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    {"end_time": "زمان پایان باید بعد از زمان شروع باشد"}
                )
        return data


class ExceptionDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExceptionDate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('is_available') and data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    {"end_time": "زمان پایان باید بعد از زمان شروع باشد"}
                )
        return data


class DoctorScheduleSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    doctor_name = serializers.CharField(read_only=True)
    weekly_schedule = WeeklyScheduleSerializer(many=True, read_only=True)
    exceptions = ExceptionDateSerializer(many=True, read_only=True)