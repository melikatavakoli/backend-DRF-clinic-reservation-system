from rest_framework import viewsets, mixins
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from users.models import Doctor, Patient
from users.serializers import (
    DoctorDetailSerializer,
    DoctorSerializer,
    PatientDetailSerializer,
    PatientSerializer,
    UserAvatarSerializer,
)
from rest_framework.viewsets import ReadOnlyModelViewSet


class DoctorViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Doctor.objects.select_related("base_user").all()
    serializer_class = DoctorSerializer
    permission_classes = [AllowAny]


class PatientViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Patient.objects.select_related("base_user").all()
    serializer_class = PatientSerializer
    permission_classes = [AllowAny]


class UserAvatarUpdateView(generics.UpdateAPIView):
    serializer_class = UserAvatarSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            request.user,
            data={"avatar": request.data.get("avatar")},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Avatar updated successfully"})


class DoctorReadOnlyViewView(ReadOnlyModelViewSet):
    serializer_class = DoctorDetailSerializer
    permission_classes = [AllowAny]
    queryset = Doctor.objects.select_related("base_user").all()


class PatientReadOnlyViewView(ReadOnlyModelViewSet):
    serializer_class = PatientDetailSerializer
    permission_classes = [AllowAny]
    queryset = Patient.objects.select_related("base_user").all()
