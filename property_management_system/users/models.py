from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    class RoleChoices(models.IntegerChoices):
        TENANT = 1,
        LANDLORD = 2,
        ADMINISTRATOR = 3

    username = None
    email = models.EmailField(_("email address"), unique=True)
    role = models.IntegerField(
        choices=RoleChoices.choices,
        default=RoleChoices.TENANT
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()



    def __str__(self):
        return self.email


class Landlord(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    contact_info = models.TextField()

    def __str__(self):
        return self.name


class Tenant(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    contact_info = models.TextField()

    def __str__(self):
        return self.name
