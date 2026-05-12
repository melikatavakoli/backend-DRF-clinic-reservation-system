from django.contrib import admin
from common.admin import BaseAdmin
from .models import BaseUser


@admin.register(BaseUser)
class BaseUserAdmin(BaseAdmin):
    list_display = (
        "id",
        "full_name",
        "mobile",
        "email",
        "role",
        "is_verified",
        "is_email_verified",
        "city",
        "country",
        "created_at_display",
    )

    list_filter = (
        "role",
        "is_verified",
        "is_email_verified",
        "country",
        "state",
        "city",
        "_created_at",
    )

    search_fields = (
        "mobile",
        "email",
        "first_name",
        "last_name",
    )

    readonly_fields = (
        "_created_at",
        "_updated_at",
        "password_updated_at",
    )

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "mobile",
                "email",
                "first_name",
                "last_name",
                "birth_date",
                "role",
                "description",
            )
        }),
        ("Location", {
            "fields": (
                "country",
                "state",
                "city",
            )
        }),
        ("Verification", {
            "fields": (
                "is_verified",
                "is_email_verified",
            )
        }),
        ("Security", {
            "fields": (
                "password",
                "password_updated_at",
                "last_login",
                "last_login_ip",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    ordering = ("_created_at",)
