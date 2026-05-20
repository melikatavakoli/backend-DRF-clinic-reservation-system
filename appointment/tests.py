from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from calendar_app.serializers import AppointmentListSerializer
from calendar_app.models import AppointmentCalender
from calendar_app.models import CustomStatus
from calendar_app.views import CustomStatusViewSet
from patient.models import Patient
from finance.utils import get_patient_financial_status_label


class CustomStatusFilterTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            mobile="09120000111",
            password="Secret123!",
            first_name="Calendar",
            last_name="Tester",
        )
        CustomStatus.objects.create(title="Done", status="done")
        CustomStatus.objects.create(title="Pending", status="pending")
        CustomStatus.objects.create(title="Cancelled", status="cancelled")

    def test_custom_status_filter_supports_repeated_status_params(self):
        request = APIRequestFactory().get(
            "/calender/custom-status/?status=done&status=pending"
        )
        force_authenticate(request, user=self.user)

        response = CustomStatusViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["status"] for item in response.data}, {"done", "pending"})

    def test_custom_status_filter_supports_csv_status_param(self):
        request = APIRequestFactory().get("/calender/custom-status/?status=done,pending")
        force_authenticate(request, user=self.user)

        response = CustomStatusViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["status"] for item in response.data}, {"done", "pending"})


class AcceptancePatientFinancialStatusSerializerTests(TestCase):
    def test_patient_financial_status_is_included_in_appointment_list_payload(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            mobile="09120000112",
            password="Secret123!",
            first_name="Patient",
            last_name="One",
        )
        patient = Patient.objects.create(user=user)
        appointment = AppointmentCalender.objects.create(patient=patient)

        data = AppointmentListSerializer(appointment).data

        self.assertEqual(
            data["patient"]["financial_status"],
            get_patient_financial_status_label(patient.id),
        )
