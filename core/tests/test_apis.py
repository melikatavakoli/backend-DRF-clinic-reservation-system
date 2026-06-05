from django.urls import path, include, reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from django.urls import reverse

from core.models import BaseUser


class AuthAPITests(APITestCase):

    def setUp(self):
        self.mobile = "09123456789"
        self.password = "Test12345"

        self.user = BaseUser.objects.create_user(
            mobile=self.mobile,
            password=self.password,
            first_name="Ali",
            last_name="Ahmadi",
            is_verified=True
        )

    # -------------------------
    # LOGIN TEST
    # -------------------------
    def test_login_success(self):
        url = reverse("core:auth_login")

        data = {
            "mobile": self.mobile,
            "password": self.password
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    # -------------------------
    # INVALID LOGIN
    # -------------------------
    def test_login_invalid_password(self):
        url = reverse("core:auth_login")

        data = {
            "mobile": self.mobile,
            "password": "wrongpass"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)

    # -------------------------
    # REGISTER (NO OTP CODE)
    # -------------------------
    def test_register_user(self):
        url = reverse("core:auth_register")

        data = {
            "mobile": "09111111111",
            "password": "Test12345",
            "re_password": "Test12345",
            "first_name": "Reza",
            "last_name": "Karimi"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(BaseUser.objects.filter(mobile="09111111111").exists())

    # -------------------------
    # OTP SEND (MOCK REDIS + CELERY)
    # -------------------------
    @patch("core.serializers.get_redis_connection")
    @patch("core.serializers.send_registry_sms.delay")
    def test_send_otp_register(self, mock_sms, mock_redis):
        url = reverse("core:auth_send_otp")

        mock_conn = mock_redis.return_value
        mock_conn.setex.return_value = True

        data = {
            "mobile": "09122222222",
            "mode": "register"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        mock_conn.setex.assert_called()
        mock_sms.assert_called()

    # -------------------------
    # RESET PASSWORD FLOW
    # -------------------------
    @patch("core.serializers.get_redis_connection")
    def test_reset_password(self, mock_redis):
        url = reverse("core:password_reset")

        mock_conn = mock_redis.return_value
        mock_conn.get.return_value = b"123456"

        data = {
            "mobile": self.mobile,
            "code": "123456",
            "password": "NewPass123",
            "re_password": "NewPass123"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)

    # -------------------------
    # CHANGE PASSWORD (AUTH REQUIRED)
    # -------------------------
    def test_change_password_unauthorized(self):
        url = reverse("core:password_change")

        data = {
            "current_password": self.password,
            "password": "NewPass123",
            "re_password": "NewPass123"
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, 401)