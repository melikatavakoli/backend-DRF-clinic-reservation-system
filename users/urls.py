from rest_framework.routers import DefaultRouter
from .views import (
    DoctorReadOnlyViewView,
    DoctorViewSet,
    PatientReadOnlyViewView,
    PatientViewSet,
    UserAvatarUpdateView,
)
from django.urls import path

app_name = "users"

router = DefaultRouter()

router.register(r"doctors", DoctorViewSet, basename="doctor")
router.register(r"patients", PatientViewSet, basename="patient")

router.register(r"detail-patient", PatientReadOnlyViewView, basename="detail_patient")
router.register(r"detail-doctor", DoctorReadOnlyViewView, basename="detail_doctor")

urlpatterns = router.urls

urlpatterns = router.urls + [
    path(
        "profile-avatar/",
        UserAvatarUpdateView.as_view(),
        name="profile-avatar",
    ),
]
