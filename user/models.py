from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from common.models import GenericModel
from user.type import BloodTypeChoices, DoctorType, EducationStatus, GenderChoices, MaritalStatus
from django.db import models

User = get_user_model()


class Doctor(GenericModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_staff",null=True,blank=True)
    title = models.CharField(max_length=400, null=True, blank=True)
    type = models.CharField(choices=DoctorType.choices, max_length=100, null=True, blank=True,)
    specialty = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_present=models.BooleanField(default=True)
    medical_code = models.CharField(max_length=50, unique=True)
    experience_years = models.PositiveIntegerField(default=0)
    consultation_fee = models.PositiveIntegerField(null=True, blank=True)
    visit_duration = models.PositiveIntegerField(help_text="duration in minutes", default=20)
    
    class Meta:
        verbose_name = "doctors"
        verbose_name_plural = "doctors"
        ordering = ('-_updated_at',)
        db_table = 'doctors'
            
    def save(self, *args, **kwargs):
        previous_state = None
        if self.pk:
            previous_state = (
                User.all_objects
                .filter(pk=self.pk)
                .values("role_id", "_is_deleted")
                .first()
            )
        super().save(*args, **kwargs)
        if previous_state is None:
            self.sync_role_profiles()
            return
        role_changed = previous_state.get("role_id") != self.role_id
        deleted_state_changed = previous_state.get("_is_deleted") != self._is_deleted
        if role_changed or deleted_state_changed:
            self.sync_role_profiles()

    def __str__(self) -> str:
        return self.core_user.full_name or None            


class Patient(GenericModel):
    user = models.OneToOne(User, on_delete=models.CASCADE, related_name='patient', null=True, blank=True)
    description = models.TextField(max_length=300, null=True, blank=True,)
    is_active=models.BooleanField(null=True, blank=True,)
    gender = models.CharField(choices=GenderChoices.choices, max_length=100, null=True, blank=True,)
    education = models.CharField(choices=EducationStatus.choices, max_length=310, null=True, blank=True,)
    job = models.CharField(max_length=310, null=True, blank=True,)
    marital_status = models.CharField(choices=MaritalStatus.choices,max_length=310,null=True,blank=True,)
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    blood_type = models.CharField(max_length=5, null=True, blank=True, choices=BloodTypeChoices.choices)
    emergency_contact = models.CharField(max_length=15, blank=True)
    insurance_number = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "patient"
        verbose_name_plural = "patients"
        db_table = 'patient'
        ordering = ('-_updated_at',)

    def __str__(self):
        if self.user:
            return self.user.full_name or "none"
        return "none"
