from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(
    r"weekly-schedule",
    views.WeeklyScheduleViewSet,
    basename="weekly-schedule",
)
router.register(r"exceptions", views.ExceptionDateViewSet, basename="exception")
router.register(
    r"doctor-schedule",
    views.DoctorScheduleViewSet,
    basename="doctor-schedule",
)

urlpatterns = [
    path("", include(router.urls)),
]
