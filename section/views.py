from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import SectionRoom
from .serializers import SectionRoomSerializer
from common.paginations import CustomLimitOffsetPagination


class SectionRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SectionRoomSerializer
    queryset = SectionRoom.objects.all()
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = ('title',)
    search_fields = ('title',)