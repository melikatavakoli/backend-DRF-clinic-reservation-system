from django.contrib import admin
from .models import WeeklySchedule, ExceptionDate


@admin.register(WeeklySchedule)
class WeeklyScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "doctor",
        "weekday",
        "start_time",
        "end_time",
        "slot_length",
        "active",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "doctor",
        "weekday",
        "active",
    )
    search_fields = (
        "doctor__first_name",
        "doctor__last_name",
        "doctor__phone",
    )
    ordering = ("doctor", "weekday", "start_time")

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Doctor", {"fields": ("doctor",)}),
        (
            "Schedule",
            {
                "fields": (
                    "weekday",
                    "start_time",
                    "end_time",
                    "slot_length",
                    "active",
                )
            },
        ),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ExceptionDate)
class ExceptionDateAdmin(admin.ModelAdmin):
    list_display = (
        "doctor",
        "date",
        "is_available",
        "start_time",
        "end_time",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "doctor",
        "is_available",
        "date",
    )
    search_fields = (
        "doctor__first_name",
        "doctor__last_name",
        "doctor__phone",
    )
    ordering = ("doctor", "date")

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Doctor", {"fields": ("doctor",)}),
        (
            "Exception Date",
            {"fields": ("date", "is_available", "start_time", "end_time")},
        ),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )
