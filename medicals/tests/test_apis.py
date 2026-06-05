from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from section.models import SectionRoom
from users.models import Doctor
from core.models import BaseUser


class SectionAPITests(APITestCase):

    def setUp(self):
        self.user = BaseUser.objects.create_user(
            mobile="09123456789",
            password="123456",
            first_name="John",
            last_name="Doe",
            is_staff=True,
        )

        self.client.force_authenticate(user=self.user)

        self.doctor = Doctor.objects.create(
            base_user=self.user,
            medical_code="DOC123",
        )

        self.section = SectionRoom.objects.create(
            title="Cardiology",
            doctor=self.doctor
        )

        self.url = "/api/v1/section/section/"

    def test_list_sections(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_section(self):
        payload = {
            "title": "Neurology",
            "doctor": self.doctor.id
        }

        res = self.client.post(self.url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_filter_by_title(self):
        res = self.client.get(self.url + "?title=Cardiology")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_search_section(self):
        res = self.client.get(self.url + "?search=Cardio")
        self.assertEqual(res.status_code, status.HTTP_200_OK)