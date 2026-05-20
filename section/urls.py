from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'section', views.SectionRoomViewSet, basename='section')

app_name = 'section'

urlpatterns = [
    path('', include(router.urls)),
]
