from django.contrib import admin
from .models import Appointment, AppointmentBlock


class AppointmentBlockInline(admin.TabularInline):
    model = AppointmentBlock
    extra = 0
    fields = ("start_time", "end_time")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "patient",
        "doctor",
        "medical_service",
        "category",
        "section",
        "date",
        "time",
        "status",
        "type",
        "is_pass",
        "is_fixed",
    )

    list_filter = (
        "status",
        "type",
        "is_pass",
        "is_fixed",
        "doctor",
        "section",
        "medical_service",
        "category",
        "date",
    )

    search_fields = (
        "title",
        "patient__first_name",
        "patient__last_name",
        "doctor__first_name",
        "doctor__last_name",
    )

    date_hierarchy = "date"

    readonly_fields = (
        "title",
    )

    inlines = [AppointmentBlockInline]

    ordering = ("-date", "-time")


@admin.register(AppointmentBlock)
class AppointmentBlockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "start_time",
        "end_time",
    )

    list_filter = (
        "start_time",
        "end_time",
    )

    search_fields = (
        "appointment__title",
        "appointment__patient__first_name",
        "appointment__patient__last_name",
    )

    autocomplete_fields = ("appointment",)
