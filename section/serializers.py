from rest_framework import serializers

from core.serializers import BaseUserSerializer
from section.models import SectionRoom


class SectionRoomSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = SectionRoom
        fields = BaseUserSerializer.Meta.fields + (
            "id", 
            "title",
            "doctor",
        )
