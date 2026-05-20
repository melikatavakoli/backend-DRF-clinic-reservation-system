from rest_framework import serializers
from django.core.exceptions import ValidationError


class NullableDateField(serializers.DateField):
    def to_internal_value(self, value):
        if value in ("", None):
            return None
        return super().to_internal_value(value)


class NullableTimeField(serializers.TimeField):
    def to_internal_value(self, value):
        if value in ("", None):
            return None
        return super().to_internal_value(value)
    
    
def _normalize_optional_bool(value):
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False
    raise ValidationError({"detail": "مقدار is_fixed باید بولی باشد"})


def _became_fixed(previous_value, current_value):
    return bool(current_value) and not bool(previous_value)