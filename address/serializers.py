from address.models import City, Country, State
from common.serializers import GenericModelSerializer


class CountrySerializer(GenericModelSerializer):
    class Meta:
        model = Country
        fields = GenericModelSerializer.Meta.fields + ("label",)


class StateSerializer(GenericModelSerializer):
    country_detail = CountrySerializer(source="country", read_only=True)

    class Meta:
        model = State
        fields = GenericModelSerializer.Meta.fields + (
            "label",
            "country",
            "country_detail",
        )


class CitySerializer(GenericModelSerializer):
    state_detail = StateSerializer(source="state", read_only=True)

    class Meta:
        model = City
        fields = GenericModelSerializer.Meta.fields + (
            "label",
            "state",
            "state_detail",
        )
