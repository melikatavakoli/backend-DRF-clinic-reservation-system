from rest_framework.routers import DefaultRouter
from users.views import DoctorViewSet, PatientViewSet, UserAvatarUpdateView
from django.urls import path

app_name='users'

router = DefaultRouter()

router.register(r"doctors", DoctorViewSet, basename="doctor")
router.register(r"patients", PatientViewSet, basename="patient")

urlpatterns = router.urls

urlpatterns = [
    path("profile-avatar/",UserAvatarUpdateView.as_view(),name="profile-avatar",),
]