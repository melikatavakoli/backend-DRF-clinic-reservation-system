import django_filters as filters

from calendar_app.models import Room
from common.filters import UUIDInFilter


class RoomFilter(filters.FilterSet):
    section = UUIDInFilter(field_name="section")
    number = UUIDInFilter(field_name="number")
    doctor = UUIDInFilter(field_name="doctor")
    dr_assist = UUIDInFilter(field_name="dr_assist")
    section__staff = UUIDInFilter(field_name="section__staff")

    class Meta:
        model = Room
        fields = ("section", "number", "doctor", "dr_assist", "section__staff")
