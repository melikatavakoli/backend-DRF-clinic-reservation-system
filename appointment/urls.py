from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'appointment', views.AppointmentViewSet, basename='appointment')

app_name = 'calender_app'

urlpatterns = [
    path("", include(router.urls)),
    path('appointments/empty/',views.AllAvailableAppointmentsAPIView.as_view(),name='appointments-empty-by-date'),
    path('appointments/doctor-day/',views.DoctorDayOverviewAPIView.as_view(),name='appointments-doctor-day'),
    path('appointments-month/range/', views.AppointmentsMonthRangeAPIView.as_view(), name='appointments-month-range'),
    path('doctor-appointments-empty/<uuid:doctor_id>/',views.DoctorAvailableAppointmentsAPIView.as_view(),name='doctor-empty-by-date'),
    path('doctor-available-hours/<uuid:doctor_id>/',views.DoctorFreeSlotsAPIView.as_view(),name='doctor-available-hours'),
    path('appointments/',views.AppointmentCreateAPIView.as_view(),name='appointment_create'),
    path('appointments-update/<uuid:pk>/',views.AppointmentUpdateAPIView.as_view(),name='appointment_update'),
    path('appointments-list/', views.AppointmentListView.as_view(), name='appointment_list'),
    path("next-appointment/", views.NextAppointmentView.as_view(), name="next_appointment"),
]
