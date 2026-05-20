from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import GenericModel
from users.models import Doctor


class SectionRoom(GenericModel):
    title = models.CharField(max_length=400,null=True,blank=True)
    doctor = models.ForeignKey(
        Doctor,
        related_name="section_staff",
        verbose_name=_("doctor"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "section"
        verbose_name_plural = "section"
        ordering = ('-_updated_at',)
        db_table = 'section'

    def __str__(self) -> str:
        return self.title or "None"