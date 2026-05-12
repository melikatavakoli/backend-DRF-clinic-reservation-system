from address.models import City, Country, State
from common.format import calculate_age, common_datetime_str
from common.managers import UserManager
from common.models import GenericModel
from django.db import models
from core.types import RoleType


class BaseUser(GenericModel):
    username = None
    mobile = models.CharField(max_length=11, unique=True)
    email = models.EmailField(blank=True, default="")
    birth_date = models.DateField(blank=True, null=True)
    role = models.CharField(max_length=1, choices=RoleType.choices, default=RoleType.PATIENT)
    description = models.TextField(blank=True, default="")
    password_updated_at = models.DateTimeField(blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "base_user"
        verbose_name_plural = "base_users"
        db_table = "base_user"

        def __str__(self):
            return self.full_name or self.mobile
    
    USERNAME_FIELD = "mobile"
    REQUIRED_FIELDS = []

    objects = UserManager(alive_only=True)

    @property
    def full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else "Anonymous"

    @property
    def age(self):
        return calculate_age(self.birth_date)

    @property
    def created_at_display(self):
        return common_datetime_str(self.created_at)

    @property
    def is_patient(self):
        return self.role == RoleType.PATIENT
    
    @property
    def is_doctor(self):
        return self.role == RoleType.DOCTOR
    
    @property
    def is_staff_user(self):
        return self.role in [RoleType.ADMIN]
