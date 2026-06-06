import pytest
from django.contrib.auth import get_user_model
from users.models import Doctor, Patient

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(
        mobile="09120000000",
        password="test123456",
        first_name="John",
        last_name="Doe",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def doctor(user):
    return Doctor.objects.create(
        base_user=user,
        medical_code="DOC001",
        specialty="Cardiology",
        experience_years=5,
    )


@pytest.fixture
def patient(user):
    return Patient.objects.create(
        base_user=user,
        gender="M",
        job="Developer",
    )