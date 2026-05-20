from django.db import models


class GenderChoices(models.TextChoices):
    MALE = "M", "Male"
    FEMALE = "F", "Female"


class MaritalStatus(models.TextChoices):
    SINGLE = "S", "Single"
    MARRIED = "M", "Married"


class EducationStatus(models.TextChoices):
    DIPLOMA = "D", "Diploma"
    ASSOCIATE = "AS", "Associate Degree"
    BACHELOR = "B", "Bachelor's Degree"
    MASTER = "M", "Master's Degree"
    PHD = "PHD", "PhD"


class DoctorType(models.TextChoices):
    VISIT = "V", "Consultation"
    SERVICES = "S", "Medical Services"


class BloodTypeChoices(models.TextChoices):
    A_POSITIVE = "A+", "A Positive"
    A_NEGATIVE = "A-", "A Negative"
    B_POSITIVE = "B+", "B Positive"
    B_NEGATIVE = "B-", "B Negative"
    AB_POSITIVE = "AB+", "AB Positive"
    AB_NEGATIVE = "AB-", "AB Negative"
    O_POSITIVE = "O+", "O Positive"
    O_NEGATIVE = "O-", "O Negative"
