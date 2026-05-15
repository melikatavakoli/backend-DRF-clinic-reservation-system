from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Doctor, Patient
from common.serializers import GenericModelSerializer
from users.models import Doctor
from users.services import pick_serializer_fields

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "full_name",
            "mobile",
            "email",
            "birth_date",
            "avatar",
            "password",
        )
        read_only_fields = ("id", "full_name")


class BaseProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(source="base_user")
    role = None

    def create(self, validated_data):
        user_data = validated_data.pop("base_user")
        password = user_data.pop("password", None)
        user = User.objects.create_user(
            role=self.role, password=password, **user_data
        )
        instance = self.Meta.model.objects.create(user=user, **validated_data)
        return instance

    def update(self, instance, validated_data):
        user_data = validated_data.pop("base_user", None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                if attr == "password":
                    user.set_password(value)
                elif attr == "avatar":
                    if value is None and user.avatar:
                        user.avatar.delete(save=False)
                    user.avatar = value
                else:
                    setattr(user, attr, value)
            user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PatientSerializer(BaseProfileSerializer):
    role = "P"

    class Meta:
        model = Patient
        fields = (
            "id",
            "user",
            "gender",
            "education",
            "job",
            "marital_status",
            "height",
            "weight",
            "blood_type",
            "emergency_contact",
            "insurance_number",
            "description",
            "is_active",
        )


class DoctorSerializer(BaseProfileSerializer):
    role = "D"

    class Meta:
        model = Doctor
        fields = (
            "id",
            "user",
            "title",
            "specialty",
            "medical_code",
            "experience_years",
            "consultation_fee",
            "visit_duration",
            "is_active",
            "is_present",
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(
        required=False,
        allow_null=True,
        use_url=False,
    )

    class Meta:
        model = User
        fields = ("avatar",)

    def update(self, instance, validated_data):
        avatar = validated_data.get("avatar", serializers.empty)
        if avatar is not serializers.empty:
            if avatar is None and instance.avatar:
                instance.avatar.delete(save=False)
            instance.avatar = avatar
            instance.save(update_fields=["avatar"])
        return instance


class DoctorDetailSerializer(GenericModelSerializer):
    UserInfoSerializer = pick_serializer_fields(
        UserSerializer,
        (
            "first_name",
            "last_name",
            "full_name",
            "mobile",
            "email",
            "birth_date",
        ),
    )
    user = UserInfoSerializer(source="base_user", read_only=True)
    info = DoctorSerializer(source="*", read_only=True)

    class Meta:
        model = Doctor
        fields = (
            "user",
            "info",
        )


class PatientDetailSerializer(GenericModelSerializer):
    UserInfoSerializer = pick_serializer_fields(
        UserSerializer,
        (
            "first_name",
            "last_name",
            "full_name",
            "mobile",
            "email",
            "birth_date",
        ),
    )
    user = UserInfoSerializer(source="*", read_only=True)
    info = PatientSerializer(source="*", read_only=True)

    class Meta:
        model = Patient
        fields = (
            "user",
            "info",
        )
