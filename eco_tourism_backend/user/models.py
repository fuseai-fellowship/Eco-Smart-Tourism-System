from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_active = models.BooleanField(default=False)  # User is inactive until email verification
    is_tourist = models.BooleanField(default=False)
    is_organiser = models.BooleanField(default=False)
