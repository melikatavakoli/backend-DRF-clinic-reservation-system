from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'services', views.MedicalServicesViewSet, basename='services')
router.register(r'line', views.LineViewSet, basename='line')
router.register(r'materials', views.MaterialsViewSet, basename='materials')
router.register(r'brand', views.BrandViewSet, basename='brand')
router.register(r'category', views.CategoryViewSet, basename='category')
router.register(r'size', views.SizeViewSet, basename='size')

app_name = 'medicals'

urlpatterns = [
    path('', include(router.urls)),
]
