from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from common.paginations import CustomLimitOffsetPagination
from common.views import BaseModelViewSet
from medicals.filters import MedicalServicesFilter
from medicals.models import MedicalServices, Line, Category
from medicals.serializers import (
    MedicalServiceSerializer,
    LineSerializer,
    CategorySerializer,
)

User = get_user_model()


class CategoryViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.select_related("section")
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = (
        "title",
        "section",
    )
    search_fields = ("title",)

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        if "is_active" not in self.request.data:
            serializer.save(is_active=False)
        else:
            serializer.save()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        if "is_active" not in self.request.data:
            serializer.save(is_active=False)
        else:
            serializer.save()


class MedicalServicesViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MedicalServiceSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_class = MedicalServicesFilter
    ordering_fields = (
        "title",
        "_updated_at",
    )
    search_fields = ("title",)

    queryset = MedicalServices.objects.select_related(
        "line",
        "category",
    ).order_by("title", "id")

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, category__is_active=True)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        if "is_active" not in self.request.data:
            serializer.save(is_active=False)
        else:
            serializer.save()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        if "is_active" not in self.request.data:
            serializer.save(is_active=False)
        else:
            serializer.save()


class LineViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LineSerializer
    queryset = Line.objects.all()
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ("title",)
    search_fields = ("title",)
