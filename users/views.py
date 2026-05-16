from rest_framework import viewsets, permissions
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import Doctor, Patient
from users.serializers import (
    DoctorSerializer,
    PatientSerializer,
    UserAvatarSerializer,
)


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.select_related("user").all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        specialty = self.request.query_params.get("specialty")
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
        return queryset
    
    
class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.select_related("user").all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        mobile = self.request.query_params.get("mobile")
        if mobile:
            queryset = queryset.filter(user__mobile__icontains=mobile)
        return queryset


class UserAvatarUpdateView(generics.UpdateAPIView):
    serializer_class = UserAvatarSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            request.user,
            data={"avatar": request.data.get("avatar")},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Avatar updated successfully"})
