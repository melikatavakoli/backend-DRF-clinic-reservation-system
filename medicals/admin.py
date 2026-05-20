from django.contrib import admin
from .models import MedicalServices


@admin.register(MedicalServices)
class SectionRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "_created_at", "_updated_at")