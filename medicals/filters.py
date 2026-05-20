from django_filters import rest_framework as filters

from .models import MedicalServices

class MedicalServicesFilter(filters.FilterSet):

    class Meta:
        model = MedicalServices
        fields = ['title', 'category', 'line', 'materials', 'brand']
