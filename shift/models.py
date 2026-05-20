from django.db import models

from common.models import GenericModel
from shift.choices import WEEKDAYS
from users.models import Doctor


class WeeklySchedule(GenericModel):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="schedules_dr",
        null=True,
        blank=True,
    )
    weekday = models.IntegerField(
        choices=WEEKDAYS.choices, null=True, blank=True
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    slot_length = models.PositiveIntegerField(
        default=20, null=True, blank=True
    )

    class Meta:
        verbose_name = "weekly_schedule"
        verbose_name_plural = "weekly_schedule"
        db_table = "doctor_weekly_scedule"

    def __str__(self):
        return f"{self.doctor} - {self.get_weekday_display()}"


class ExceptionDate(GenericModel):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="exceptions",
        null=True,
        blank=True,
    )
    date = models.DateField()
    is_available = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = "exception_date"
        verbose_name_plural = "exception_date"
        db_table = "doctor_exception_date"

    def __str__(self):
        return f"{self.doctor} - {self.date}"
