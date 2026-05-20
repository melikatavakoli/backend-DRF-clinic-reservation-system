from django.contrib import admin

from medicals.serializers import Brand, Category, Line, Materials, Size
from .models import MedicalServices


@admin.register(MedicalServices)
class SectionRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "_created_at", "_updated_at")
    
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "_created_at", "_updated_at")
    
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "_created_at", "_updated_at")
    
@admin.register(Materials)
class MaterialsAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "_created_at", "_updated_at")
    
@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "_created_at", "_updated_at")
    
@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "_created_at", "_updated_at")