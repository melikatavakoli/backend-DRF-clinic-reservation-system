from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import BaseUser
from users.models import Doctor
from section.models import SectionRoom


class SectionAPITests(APITestCase):
    def setUp(self):
        self.base_user = BaseUser.objects.create(
            mobile="09123456789",
            first_name="John",
            last_name="Doe",
        )
        self.base_user.set_password("testpass123")
        self.base_user.save()

        self.doctor = Doctor.objects.create(
            base_user=self.base_user,
            medical_code="DOC12345",
            specialty="Cardiology",
        )

        self.client.force_authenticate(user=self.base_user)

        self.section = SectionRoom.objects.create(
            title="Neurology Room", doctor=self.doctor
        )

        self.list_url = reverse("section:section-list")

    def test_list_sections(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_section(self):
        payload = {"title": "Cardiology Room", "doctor": self.doctor.id}

        response = self.client.post(self.list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SectionRoom.objects.count() >= 1, True)

    def test_filter_by_title(self):
        response = self.client.get(self.list_url, {"title": "Neurology Room"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_section(self):
        response = self.client.get(self.list_url, {"search": "Neuro"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
