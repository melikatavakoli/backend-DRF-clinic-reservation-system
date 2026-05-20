from rest_framework import serializers

from core.serializers import BaseUserSerializer
from medicals.models import (
    MedicalServices, Materials, 
    Brand, Line, 
    Category, Size
    )


class MedicalServiceSerializer(BaseUserSerializer):
    material_title = serializers.CharField(source="materials.title", read_only=True)
    line_title = serializers.CharField(source="line.title", read_only=True)
    brand_title = serializers.CharField(source="brand.title", read_only=True)
    category_title = serializers.CharField(source="category.title", read_only=True)
    
    class Meta(BaseUserSerializer.Meta):
        model = MedicalServices
        fields = BaseUserSerializer.Meta.fields + (
            "title",
            'id',
            'materials',
            'material_title',
            'line',
            'line_title',
            'brand',
            'brand_title',
            'category',
            'category_title',
            "is_active"
        )


class MaterialsSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = Materials
        fields = BaseUserSerializer.Meta.fields + (
            "title", 
            'id',
            )


class SizeSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = Size
        fields = BaseUserSerializer.Meta.fields + (
            "title",
            'id'
        )


class BrandSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = Brand
        fields = BaseUserSerializer.Meta.fields + (
            "title",
            'id'
        )


class LineSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = Line
        fields = BaseUserSerializer.Meta.fields + (
            "title",
            'id'
        )


class CategorySerializer(BaseUserSerializer):
    section_title =serializers.CharField(source="section.title",read_only=True)
    
    class Meta(BaseUserSerializer.Meta):
        model = Category
        fields = BaseUserSerializer.Meta.fields + (
            "title",
            "section",
            "section_title",
            'id',
            "is_active"
        )
