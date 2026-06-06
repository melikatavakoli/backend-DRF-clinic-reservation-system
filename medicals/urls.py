from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r"services", views.MedicalServicesViewSet, basename="services")
router.register(r"line", views.LineViewSet, basename="line")
router.register(r"category", views.CategoryViewSet, basename="category")

app_name = "medicals"

urlpatterns = [
    path("", include(router.urls)),
]
