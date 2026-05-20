from django.contrib import admin
from .models import SectionRoom


@admin.register(SectionRoom)
class SectionRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "doctor", "_created_at", "_updated_at")
    list_filter = ("doctor",)
    search_fields = ("title", "doctor__first_name", "doctor__last_name", "doctor__username")
    ordering = ("-_updated_at",)
    autocomplete_fields = ("doctor",)