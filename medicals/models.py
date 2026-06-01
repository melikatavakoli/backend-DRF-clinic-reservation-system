from django.db import models
from common.models import GenericModel
from section.models import SectionRoom


class Category(GenericModel):
    section = models.ForeignKey(
        SectionRoom,
        on_delete=models.CASCADE,
        related_name="category_section",
        verbose_name = "section",
        null=True,
        blank=True
    )
    title = models.CharField(max_length=310,null=True,blank=True,)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        db_table = 'category'
        ordering = ('-_updated_at',)

    def __str__(self) -> str:
        return self.title or "None"


class Line(GenericModel):
    title = models.CharField(max_length=310,null=True,blank=True,)
    
    class Meta:
        verbose_name = "line"
        verbose_name_plural = "line"
        db_table = 'line'
        ordering = ('-_updated_at',)

    def __str__(self) -> str:
        return self.title or "None"


class MedicalServices(GenericModel):
    title = models.CharField(max_length=310,null=True,blank=True,)
    is_active = models.BooleanField(default=True)
    line = models.ForeignKey(
        Line,
        on_delete=models.CASCADE,
        related_name="services_line",
        verbose_name = "line",
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="services_category",
        verbose_name = "category",
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "medical_services"
        verbose_name_plural = "medical_services"
        ordering = ('-_updated_at',)
        db_table = 'medical_services'

    def __str__(self) -> str:
        return self.title or "none"

