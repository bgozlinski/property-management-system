import factory
from django.utils import timezone
from .models import Message
from users.factories import CustomUserFactory

"""
This module provides factory classes for creating test instances of messaging models.

These factories are used in tests to generate realistic test data for messages
with minimal setup.
"""


class MessageFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Message instances for testing.

    Generates messages with realistic content between two users.
    By default, creates unread messages with the IN_APP delivery method.
    """

    class Meta:
        """Metadata for the factory, specifying the model to create."""

        model = Message

    sender = factory.SubFactory(CustomUserFactory)
    recipient = factory.SubFactory(CustomUserFactory)
    subject = factory.Faker("sentence", nb_words=5)
    content = factory.Faker("paragraph")
    timestamp = factory.LazyFunction(timezone.now)
    read = False
    delivery_method = Message.DeliveryMethod.IN_APP
