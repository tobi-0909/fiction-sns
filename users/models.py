from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class CustomUser(AbstractUser):
    handle = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]+$',
                message='handleは英数字とアンダースコアのみ使用できます。',
            )
        ],
    )
    display_name = models.CharField(max_length=50, blank=True)
