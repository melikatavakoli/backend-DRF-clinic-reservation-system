from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'appointment', views.AppointmentViewSet, basename='appointment')

app_name = 'calender_app'

urlpatterns = [
    path("", include(router.urls)),
    path('appointments-month/range/', views.AppointmentsMonthRangeAPIView.as_view(), name='appointments-month-range'),
    path("next-appointment/", views.NextAppointmentView.as_view(), name="next_appointment"),
]
