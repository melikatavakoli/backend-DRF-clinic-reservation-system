from django.db import models

class GenderChoices(models.TextChoices):
    male = "male", "مرد"
    female = "female", "زن"

class MaritalStatus(models.TextChoices):
    single = "single", "مجرد"
    married = "married", "متاهل"

class EducationStatus(models.TextChoices):
    diploma = "diploma", "دیپلم"
    associate = "associate", "کاردانی"
    bachelor = "bachelor", "کارشناسی"
    master = "master", "کارشناسی ارشد"
    phd = "phd", "دکتری"
    
class DoctorType(models.TextChoices):
    VISIT = "visit", "ویزیت"
    SERVICES = "services", "خدمات"
    
class BloodTypeChoices(models.TextChoices):
    A_POSITIVE = "A+", "A Positive"
    A_NEGATIVE = "A-", "A Negative"
    B_POSITIVE = "B+", "B Positive"
    B_NEGATIVE = "B-", "B Negative"
    AB_POSITIVE = "AB+", "AB Positive"
    AB_NEGATIVE = "AB-", "AB Negative"
    O_POSITIVE = "O+", "O Positive"
    O_NEGATIVE = "O-", "O Negative"