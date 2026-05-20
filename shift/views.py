from rest_framework import generics, status
from rest_framework.response import Response
from shift.models import WeeklySchedule
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q

from shift.serializers import ( WeeklyScheduleSerializer, DoctorExceptionDateSerializer )
from users.models import Doctor


class StaffWeeklyScheduleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, doctor_id):
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({"detail": "دکتر یافت نشد."}, status=404)
        schedules = WeeklySchedule.objects.filter(
            doctor=doctor, active=True
        ).order_by("weekday")
        if not schedules.exists():
            return Response(
                {
                    "doctor_id": str(doctor.id),
                    "doctor_name": str(doctor),
                    "specialty": getattr(doctor, "specialty", None),
                    "message": "برای این دکتر هنوز برنامه کاری تعریف نشده است.",
                    "schedules": [],
                }
            )

        serializer = WeeklyScheduleSerializer(schedules, many=True)

        persian_days = [
            "شنبه",
            "یکشنبه",
            "دوشنبه",
            "سه‌شنبه",
            "چهارشنبه",
            "پنجشنبه",
            "جمعه",
        ]
        english_days = [
            "Saturday",
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
        ]

        result = []
        for item in serializer.data:
            weekday_num = item["weekday"]
            result.append(
                {
                    "id": item["id"],
                    "active": item["active"],
                    "day_persian": persian_days[weekday_num],
                    "day_english": english_days[weekday_num],
                    "start_time": item["start_time"],
                    "end_time": item["end_time"],
                    "slot_length": item["slot_length"] or 20,
                }
            )

        return Response(
            {
                "doctor_id": str(doctor.id),
                "doctor_name": str(doctor),
                "specialty": getattr(doctor, "specialty", None),
                "schedules": result,
            }
        )


class MyWeeklyScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        doctor = getattr(user, "doctor_profile", None)

        if not doctor:
            return Response(
                {"detail": "شما به عنوان دکتر ثبت نشده‌اید."},
                status=status.HTTP_403_FORBIDDEN,
            )

        schedules = WeeklySchedule.objects.filter(doctor=doctor).order_by(
            "weekday"
        )

        if not schedules.exists():
            return Response(
                {
                    "doctor_name": str(doctor),
                    "message": "شما هیچ برنامه کاری تعریف شده‌ای ندارید.",
                    "schedules": [],
                }
            )

        serializer = WeeklyScheduleSerializer(schedules, many=True)
        persian_days = [
            "شنبه",
            "یکشنبه",
            "دوشنبه",
            "سه‌شنبه",
            "چهارشنبه",
            "پنجشنبه",
            "جمعه",
        ]

        result = []
        for item in serializer.data:
            weekday_num = int(item["weekday"])
            result.append(
                {
                    "day_persian": persian_days[weekday_num],
                    "day_english": WeeklySchedule.WEEKDAYS[weekday_num][1],
                    "start_time": item["start_time"],
                    "end_time": item["end_time"],
                    "slot_length": item.get("slot_length") or 20,
                }
            )

        return Response(
            {
                "doctor_id": doctor.id,
                "doctor_name": str(doctor),
                "schedules": result,
            }
        )


class DoctorWeeklyScheduleCreateAPIView(generics.CreateAPIView):
    serializer_class = WeeklyScheduleSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        doctor_instance = getattr(user, "doctor_profile", None)
        if not doctor_instance:
            return Response({"detail": "شما دکتر ثبت نشده‌اید."}, status=404)
        is_many = isinstance(request.data, list)
        data_list = request.data if is_many else [request.data]
        created_schedules = []

        with transaction.atomic():
            for item in data_list:
                item_data = item.copy()
                item_data.pop("staff", None)
                item_data.pop("doctor", None)
                item_data["doctor"] = doctor_instance.id
                serializer = self.get_serializer(data=item_data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                created_schedules.append(serializer.data)
        return Response(created_schedules, status=status.HTTP_201_CREATED)


class DoctorWeeklyScheduleUpdateAPIView(generics.UpdateAPIView):
    serializer_class = WeeklyScheduleSerializer
    queryset = WeeklySchedule.objects.all()
    lookup_field = "id"
    permission_classes = [IsAuthenticated]


class DoctorExceptionDateCreateAPIView(generics.CreateAPIView):
    serializer_class = DoctorExceptionDateSerializer
    permission_classes = [IsAuthenticated]
