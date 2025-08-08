import factory
from .models import Property
from users.factories import LandlordFactory


"""
This module provides factory classes for creating test instances of property models.

These factories are used in tests to generate realistic test data with minimal setup.
"""


class PropertyFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Property instances for testing.

    Generates properties with realistic addresses, cities, postal codes, and
    randomized values for area, rent, and costs. Each property is associated
    with a randomly generated landlord.
    """

    class Meta:
        """Metadata for the factory, specifying the model to create."""

        model = Property

    address = factory.Faker("street_address")
    city = factory.Faker("city")
    postal_code = factory.Faker("postcode")
    area_m2 = factory.Faker("pyfloat", min_value=20, max_value=200)
    current_rent = factory.Faker("pyfloat", min_value=500, max_value=5000)
    additional_costs = factory.Faker("pyfloat", min_value=50, max_value=500)
    status = Property.StatusChoices.AVAILABLE
    landlord = factory.SubFactory(LandlordFactory)
