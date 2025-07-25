import factory
import uuid
from django.utils import timezone
from .models import Reminder, TenantInvitation
from properties.factories import PropertyFactory
from users.factories import CustomUserFactory


"""
This module provides factory classes for creating test instances of notification models.

These factories are used in tests to generate realistic test data for reminders
and tenant invitations with minimal setup.
"""


class ReminderFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Reminder instances for testing.

    Generates reminders with realistic titles, descriptions, and due dates
    set 30 days in the future. Each reminder is associated with a randomly
    generated property.
    """

    class Meta:
        """Metadata for the factory, specifying the model to create."""

        model = Reminder

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    due_date = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(days=30)
    )
    property = factory.SubFactory(PropertyFactory)


class TenantInvitationFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating TenantInvitation instances for testing.

    Generates invitations with random email addresses, associated with a
    randomly generated property and landlord. Invitations are set to expire
    7 days in the future and have a PENDING status by default.
    """

    class Meta:
        """Metadata for the factory, specifying the model to create."""

        model = TenantInvitation

    email = factory.Faker("email")
    property_unit = factory.SubFactory(PropertyFactory)
    landlord = factory.SubFactory(CustomUserFactory, role=2)
    created_at = factory.LazyFunction(timezone.now)
    expires_at = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(days=7)
    )
    token = factory.LazyFunction(uuid.uuid4)
    status = TenantInvitation.StatusChoices.PENDING
