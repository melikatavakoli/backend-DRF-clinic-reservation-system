from django.contrib import admin
from .models import Doctor, Patient


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "base_user",
        "medical_code",
        "specialty",
        "type",
        "experience_years",
        "consultation_fee",
        "is_active",
        "is_present",
    )
    list_filter = ("is_active", "is_present", "type", "specialty")
    search_fields = (
        "medical_code",
        "base_user__full_name",
        "base_user__mobile",
    )
    ordering = ("_created_at",)

    autocomplete_fields = ("base_user",)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "base_user",
        "gender",
        "blood_type",
        "marital_status",
        "insurance_number",
        "is_active",
    )
    list_filter = ("gender", "blood_type", "marital_status", "is_active")
    search_fields = (
        "base_user__full_name",
        "base_user__mobile",
        "insurance_number",
    )
    ordering = ("_created_at",)

    autocomplete_fields = ("base_user",)
