from django.db import models


class WEEKDAYS(models.TextChoices):
    (0, "شنبه"),
    (1, "یکشنبه"),
    (2, "دوشنبه"),
    (3, "سه‌شنبه"),
    (4, "چهارشنبه"),
    (5, "پنجشنبه"),
    (6, "جمعه"),
