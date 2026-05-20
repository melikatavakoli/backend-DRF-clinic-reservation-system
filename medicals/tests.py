from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from medical_plan.models import MainService, ServicePlan
from medical_services.models import Category, MedicalServices
from user.models import Doctor


class ServicePlanCalculatePriceAPIViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            mobile="09129990001",
            password="Secret123!",
            base_role="admin",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.category = Category.objects.create(title="Implant")
        self.medical_service = MedicalServices.objects.create(
            category=self.category,
            title="Implant Service",
            price="120000",
        )
        self.main_service = MainService.objects.create()
        self.service_plan = ServicePlan.objects.create(
            main_service=self.main_service,
            category=self.category,
            service_doctor=Doctor.objects.create(),
            service_plan_price="950000",
        )

    def test_calculate_price_uses_base_source_not_latest_service_plan_override(self):
        response = self.client.get(
            f"/api/v1/medical_service/calculate-price/{self.medical_service.id}/",
            {"teeth_count": 2},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price"], 240000)
