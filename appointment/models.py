from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import timedelta, time

from appointment.types import AppointmentType, AppointmentStatus
from common.models import GenericModel
from medicals.models import MedicalServices, Category
from section.models import SectionRoom
from users.models import Doctor, Patient

User = get_user_model()


def update_appointment_is_pass(appointment):
    if (
        appointment.appointment_date
        and appointment.appointment_date < timezone.localdate()
    ):
        appointment.is_pass = True
        appointment.save(update_fields=["is_pass"])
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
        blank=True,
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="doctor_calendar",
        null=True,
        blank=True,
    )
    section = models.ForeignKey(
        SectionRoom,
        related_name="appointment_section",
        verbose_name=_("section"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    final_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False,
        default=0,
    )
    title = models.CharField(max_length=400, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=24,
        default="pending",
        choices=AppointmentStatus,
        null=True,
        blank=True,
    )
    type = models.CharField(
        choices=AppointmentType.choices,
        max_length=100,
        null=True,
        blank=True,
    )
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(
        null=True,
        blank=True,
    )
    enter_section_time = models.TimeField(
        null=True,
        blank=True,
    )
    appointment_date = models.DateField(
        null=True,
        blank=True,
    )
    appointment_start_time = models.TimeField(
        null=True,
        blank=True,
    )
    appointment_end_time = models.TimeField(
        null=True,
        blank=True,
    )
    next_appointment_date = models.DateField(
        null=True,
        blank=True,
    )
    next_appointment_time = models.TimeField(
        null=True,
        blank=True,
    )
    total_duration = models.PositiveIntegerField(null=True, blank=True)
    is_pass = models.BooleanField(null=True, blank=True)
    is_fixed = models.BooleanField(null=True, blank=True)
    is_advise = models.BooleanField(
        null=True,
        blank=True,
    )
    is_paid = models.BooleanField(
        default=False,
    )
    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
    )
    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
    )
    cancellation_reason = models.TextField(
        null=True,
        blank=True,
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    symptoms = models.TextField(
        null=True,
        blank=True,
    )
    notes = models.TextField(
        null=True,
        blank=True,
    )
    is_urgent = models.BooleanField(
        default=False,
    )
    reminder_sent = models.BooleanField(
        default=False,
    )
    duration_minutes = models.PositiveIntegerField(
        default=15,
    )

    class Meta:
        verbose_name = "appointment"
        verbose_name_plural = "appointments"
        db_table = "appointment"

    def __str__(self):
        return f"{self.patient} ({self.date} {self.time})"

    def save(self, *args, **kwargs):
        if not self.title:
            today = timezone.now().strftime("%Y%m%d")
            with transaction.atomic():
                last_appointment = (
                    Appointment.objects.select_for_update()
                    .filter(title__startswith=f"APT{today}")
                    .order_by("-title")
                    .first()
                )
                if last_appointment:
                    last_num = int(last_appointment.title[11:])
                    new_num = last_num + 1
                else:
                    new_num = 1
                self.title = f"APT{today}{str(new_num).zfill(5)}"

        self.final_amount = self.fee - self.discount_amount

        if (
            self.appointment_date
            and self.appointment_start_time
            and self.duration_minutes
        ):
            appointment_date = self.appointment_date
            if isinstance(appointment_date, str):
                appointment_date = datetime.strptime(
                    appointment_date, "%Y-%m-%d"
                ).date()

            start_time = self.appointment_start_time
            if isinstance(start_time, str):
                # پاک کردن Z و میلی‌ثانیه
                time_str = start_time.replace("Z", "")
                if "." in time_str:
                    time_str = time_str.split(".")[0]
                time_parts = time_str.split(":")
                start_time = time(
                    hour=int(time_parts[0]),
                    minute=int(time_parts[1]),
                    second=int(time_parts[2]) if len(time_parts) > 2 else 0,
                )

            start_datetime = datetime.combine(appointment_date, start_time)
            end_datetime = start_datetime + timedelta(minutes=self.duration_minutes)
            self.appointment_end_time = end_datetime.time()

        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.doctor and self.appointment_date and self.appointment_start_time:
            overlapping = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_date=self.appointment_date,
                appointment_start_time=self.appointment_start_time,
                status__in=[
                    AppointmentStatus.pending,
                    AppointmentStatus.in_clinic,
                    AppointmentStatus.in_progress,
                ],
            ).exclude(id=self.id)

            if overlapping.exists():
                raise ValidationError(
                    _("این زمان برای پزشک انتخاب شده قبلاً رزرو شده است")
                )

    def cancel(self, reason=None):
        """لغو نوبت"""
        self.status = AppointmentStatus.cancelled
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.save()
        if self.is_paid:
            self.refund_payment()

    def check_in(self):
        """ثبت مراجعه بیمار"""
        self.status = AppointmentStatus.in_progress
        self.check_in_time = timezone.now()
        self.save()

    def start_visit(self):
        """شروع ویزیت"""
        self.status = AppointmentStatus.in_progress
        self.save()

    def complete(self):
        """اتمام ویزیت"""
        self.status = AppointmentStatus.done
        self.check_out_time = timezone.now()
        self.save()

    def is_upcoming(self):
        """آیا نوبت آینده است؟"""
        if not self.appointment_date or not self.appointment_start_time:
            return False

        appointment_datetime = datetime.combine(
            self.appointment_date, self.appointment_start_time
        )

        if timezone.is_naive(appointment_datetime):
            appointment_datetime = timezone.make_aware(appointment_datetime)
        now = timezone.now()
        return appointment_datetime > now and self.status != AppointmentStatus.done

    def is_today(self):
        """آیا نوبت امروز است؟"""
        return self.appointment_date == timezone.now().date()


class AppointmentBlock(GenericModel):
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="blocks",
        null=True,
        blank=True,
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = "appointment_block"
        verbose_name_plural = "appointment_blocks"
        db_table = "appointment_block"

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"


class AppointmentReminder(models.Model):
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="reminders"
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=[
            ("sms", "SMS"),
            ("email", "Email"),
            ("push", "Push Notification"),
        ],
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "در انتظار"),
            ("sent", "ارسال شده"),
            ("failed", "ناموفق"),
        ],
        default="pending",
    )

    class Meta:
        db_table = "appointment_reminder"
