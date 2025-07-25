import factory
from .models import CustomUser, Landlord, Tenant

"""
This module provides factory classes for creating test instances of user models.

These factories are used in tests to generate realistic test data with minimal setup.
"""


class CustomUserFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating CustomUser instances for testing.

    Generates users with realistic first and last names, derived email addresses,
    and a default password of 'password123'.
    """

    class Meta:
        model = CustomUser

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(
        lambda obj: f"{obj.first_name}.{obj.last_name}@example.com"
    )
    password = factory.PostGenerationMethodCall("set_password", "password123")
    role = CustomUser.RoleChoices.TENANT
    is_active = True
    is_staff = False
    is_superuser = False


class TenantFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Tenant instances for testing.

    Creates a tenant with an associated CustomUser that has the TENANT role
    and a randomly generated phone number as contact information.
    """

    class Meta:
        model = Tenant

    user = factory.SubFactory(CustomUserFactory, role=CustomUser.RoleChoices.TENANT)
    contact_info = factory.Faker("phone_number")


class LandlordFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Landlord instances for testing.

    Creates a landlord with an associated CustomUser that has the LANDLORD role
    and a randomly generated phone number as contact information.
    """

    class Meta:
        model = Landlord

    user = factory.SubFactory(CustomUserFactory, role=CustomUser.RoleChoices.LANDLORD)
    contact_info = factory.Faker("phone_number")
