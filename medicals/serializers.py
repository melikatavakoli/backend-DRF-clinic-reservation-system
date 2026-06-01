from rest_framework import serializers

from core.serializers import BaseUserSerializer
from medicals.models import (
    MedicalServices,
    Line, 
    Category
    )


class MedicalServiceSerializer(BaseUserSerializer):
    line_title = serializers.CharField(source="line.title", read_only=True)
    category_title = serializers.CharField(source="category.title", read_only=True)
    
    class Meta(BaseUserSerializer.Meta):
        model = MedicalServices
        fields = BaseUserSerializer.Meta.fields + (
            "title",
            'id',
            'line',
            'line_title',
            'category',
            'category_title',
            "is_active"
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
