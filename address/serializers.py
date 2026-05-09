from address.models import Branch, City, Country, State
from common.serializers import GenericModelSerializer


class CountrySerializer(GenericModelSerializer):
    class Meta:
        model = Country
        fields = GenericModelSerializer.Meta.fields + (
            "label", 
        )


class CityMiniSerializer(GenericModelSerializer):
    class Meta:
        model = City
        fields = GenericModelSerializer.Meta.fields + (
            "label"
        )


class StateMiniSerializer(GenericModelSerializer):
    class Meta:
        model = State
        fields = GenericModelSerializer.Meta.fields +(
            "label"
        )


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
    state_detail = StateMiniSerializer(source="state", read_only=True)

    class Meta:
        model = City
        fields = GenericModelSerializer.Meta.fields + (
            "label",
            "state",
            "state_detail",
        )


class BranchSerializer(GenericModelSerializer):
    city_detail = CityMiniSerializer(source="city", read_only=True)
    state_detail = StateMiniSerializer(source="city.state", read_only=True)

    class Meta:
        model = Branch
        fields = GenericModelSerializer.Meta.fields + (
            "code",
            "title",
            "city",
            "city_detail",
            "address",
            "location",
            "is_active",
            "mobile",
            "state_detail",
        )
