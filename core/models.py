from address.models import City, Country, State
from common.format import calculate_age, common_datetime_str
from common.managers import SoftDeleteManager, UserManager
from common.models import GenericModel
from django.db import models
from core.types import RoleType, StatusType
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from uuid import uuid4


class BaseUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField("unique id", primary_key=True, unique=True, null=False, default=uuid4, editable=False)
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
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=StatusType.choices, default=StatusType.ACTIVE)
    _is_deleted = models.BooleanField(default=False)
    _deleted_at = models.DateTimeField(null=True, blank=True)
    password_updated_at = models.DateTimeField(null=True, blank=True,auto_now_add=True,)
    objects = UserManager(alive_only=True)
    all_objects = UserManager(alive_only=None)
    deleted_objects = UserManager(alive_only=False)

    def delete(self, using=None, keep_parents=False):
        self._is_deleted = True
        self._deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self._is_deleted = False
        self._deleted_at = None
        self.save()

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ["first_name", "last_name"]
    
    class Meta:
        verbose_name = "base_user"
        verbose_name_plural = "base_users"
        db_table = "base_user"
        indexes = (
            models.Index(fields=['id'], name='user_id_idx'),
            models.Index(fields=['mobile'], name='user_mobile_idx'),
            models.Index(fields=['first_name'], name='user_first_name_idx'),
            models.Index(fields=['last_name'], name='user_last_name_idx'),
        )
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

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
