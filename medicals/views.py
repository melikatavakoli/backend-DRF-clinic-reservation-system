from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from common.paginations import CustomLimitOffsetPagination
from medicals.filters import MedicalServicesFilter
from medicals.models import (
    MedicalServices, Brand, Line, 
    Materials, Category, Size
    )
from medicals.serializers import (
    MedicalServiceSerializer, BrandSerializer,
    LineSerializer, MaterialsSerializer, 
    CategorySerializer, SizeSerializer
    )

User = get_user_model()


class CategoryViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.select_related("section")
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ('title','section',)
    search_fields = ('title',)

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def perform_create(self, serializer):
        if 'is_active' not in self.request.data:
            serializer.save(is_active=False)
        else:
            serializer.save()

    def perform_update(self, serializer):
        if 'is_active' not in self.request.data:
            serializer.save(is_active=False)
        else:
            serializer.save()


class MedicalServicesViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MedicalServiceSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_class = MedicalServicesFilter
    ordering_fields = ('title', '_updated_at',)
    search_fields = ('title',)

    queryset = MedicalServices.objects.select_related(
        "materials",
        "line",
        "brand",
        "category",
    ).order_by("title", "id")
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, category__is_active=True)

    def perform_create(self, serializer):
        if 'is_active' not in self.request.data:
            serializer.save(is_active=False)
        else:
            serializer.save()

    def perform_update(self, serializer):
        if 'is_active' not in self.request.data:
            serializer.save(is_active=False)
        else:
            serializer.save()
            

class LineViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LineSerializer
    queryset = Line.objects.all()
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ('title',)
    search_fields = ('title',)


class MaterialsViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MaterialsSerializer
    queryset = Materials.objects.all()
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ('title',)
    search_fields = ('title',)


class BrandViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ('title',)
    search_fields = ('title',)


class SizeViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SizeSerializer
    queryset = Size.objects.all()
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ('title',)
    search_fields = ('title',)