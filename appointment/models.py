from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Max
from django.db import models, transaction

from appointment.types import AppointmentType, AppointmentStatus
from common.models import GenericModel
from medicals.models import MedicalServices, Category
from section.models import SectionRoom
from users.models import Doctor, Patient

User = get_user_model()


def update_appointment_is_pass(appointment):
    if appointment.appointment_date and appointment.appointment_date < timezone.localdate():
        appointment.is_pass = True
        appointment.save(update_fields=['is_pass'])
    return appointment.is_pass


class Appointment(GenericModel):
    medical_service = models.ForeignKey(
        MedicalServices,
        related_name="appointment_service",
        verbose_name=("medical_service"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        related_name="appointment_category",
        verbose_name=("medical_service"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="patient_appointment",
        null=True,
        blank=True
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="doctor_calendar",
        null=True,
        blank=True
    )
    section = models.ForeignKey(
        SectionRoom,
        related_name="appointment_section",
        verbose_name=_("section"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=400,null=True,blank=True)
    number = models.IntegerField(null=True,blank=True)
    status = models.CharField(max_length=24,default="pending",choices=AppointmentStatus,null=True,blank=True)
    type = models.CharField(choices=AppointmentType.choices,max_length=100,null=True,blank=True,)
    date = models.DateField(null=True,blank=True)
    time = models.TimeField(null=True,blank=True,)
    enter_section_time = models.TimeField(null=True,blank=True,)
    appointment_date = models.DateField(null=True,blank=True,)
    appointment_start_time = models.TimeField(null=True,blank=True,)
    appointment_end_time = models.TimeField(null=True,blank=True,)
    next_appointment_date = models.DateField(null=True,blank=True,)
    next_appointment_time = models.TimeField(null=True,blank=True,)
    total_duration = models.PositiveIntegerField(null=True,blank=True)
    is_pass = models.BooleanField(null=True,blank=True)
    is_fixed = models.BooleanField(null=True,blank=True)
    is_advise = models.BooleanField(null=True,blank=True,)
    
    class Meta:
        verbose_name = "appointment"
        verbose_name_plural = "appointments"
        db_table = 'appointment'

    def __str__(self):
        return f"{self.patient} ({self.date} {self.time})"

    def save(self, *args, **kwargs):
        if not self.title:
            with transaction.atomic():
                last_title = (
                    Appointment.objects
                    .select_for_update()
                    .aggregate(max_title=Max("title"))
                    ["max_title"]
                )
                if last_title and str(last_title).isdigit():
                    self.title = str(int(last_title) + 1)
                else:
                    self.title = "1000"
        super().save(*args, **kwargs)



class AppointmentBlock(GenericModel):
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="blocks",
        null=True,
        blank=True
    )
    start_time = models.TimeField(null=True,blank=True)
    end_time = models.TimeField(null=True,blank=True)

    class Meta:
        verbose_name = "appointment_block"
        verbose_name_plural = "appointment_blocks"
        db_table = 'appointment_block'

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"
