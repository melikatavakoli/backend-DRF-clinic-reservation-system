from address.models import City, Country, State
from common.serializers import BaseUserSerializer


class CountrySerializer(BaseUserSerializer):
    class Meta:
        model = Country
        fields = BaseUserSerializer.Meta.fields + ("label",)


class StateSerializer(BaseUserSerializer):
    country_detail = CountrySerializer(source="country", read_only=True)

    class Meta:
        model = State
        fields = BaseUserSerializer.Meta.fields + (
            "label",
            "country",
            "country_detail",
        )


class CitySerializer(BaseUserSerializer):
    state_detail = StateSerializer(source="state", read_only=True)

    class Meta:
        model = City
        fields = BaseUserSerializer.Meta.fields + (
            "label",
            "state",
            "state_detail",
        )
