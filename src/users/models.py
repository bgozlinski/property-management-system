from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


"""
This module provides models for user management in the Property Management System.
It includes custom user model and related models for different user roles.
"""


class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.

    Uses email as the unique identifier instead of username and adds a role field
    to distinguish between tenants, landlords, and administrators.
    """

    class RoleChoices(models.IntegerChoices):
        """Defines the possible roles for a user in the system."""

        TENANT = (1,)
        LANDLORD = (2,)
        ADMINISTRATOR = 3

    username = None
    email = models.EmailField(_("email address"), unique=True)
    role = models.IntegerField(choices=RoleChoices.choices, default=RoleChoices.TENANT)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        """Return the email as the string representation of the user."""
        return self.email


class Landlord(models.Model):
    """
    Model representing a landlord in the system.

    A landlord is associated with a CustomUser and can own multiple properties.
    """

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    contact_info = models.TextField()
    # ISO 3166-1 alpha-2 country code for tax residency (e.g., "PL" for Poland)
    tax_residency_country = models.CharField(max_length=2, default="PL")

    def __str__(self):
        """Return the name as the string representation of the landlord."""
        return self.name


class Tenant(models.Model):
    """
    Model representing a tenant in the system.

    A tenant is associated with a CustomUser and can rent properties.
    """

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    contact_info = models.TextField()

    def __str__(self):
        """Return the name as the string representation of the tenant."""
        return self.name
