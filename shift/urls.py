from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()


urlpatterns = [
    path("", include(router.urls)),
    path(
        "shift/",
        views.MyWeeklyScheduleAPIView.as_view(),
        name="my-weekly-schedule",
    ),
    path(
        "shift-details/<uuid:doctor_id>/",
        views.StaffWeeklyScheduleDetailAPIView.as_view(),
        name="staff-schedule-detail",
    ),
    path(
        "schedule/<uuid:doctor_id>/",
        views.DoctorWeeklyScheduleCreateAPIView.as_view(),
        name="doctor-shift-create",
    ),
    path(
        "schedule-update/<uuid:doctor_id>/<uuid:id>/",
        views.DoctorWeeklyScheduleUpdateAPIView.as_view(),
        name="doctor-shift-update",
    ),
    path(
        "special-days/<uuid:doctor_id>/",
        views.DoctorExceptionDateCreateAPIView.as_view(),
        name="doctor-special-day-create",
    ),
]
