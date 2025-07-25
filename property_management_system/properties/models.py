from django.db import models

from users.models import Landlord


"""
This module provides models for property management in the system.

It includes the Property model for storing information about real estate properties
managed by landlords in the system.
"""


class Property(models.Model):
    """
    Model representing a real estate property in the system.

    A property is owned by a landlord and can be in various states (available,
    rented, under maintenance, or unavailable). It stores information about
    the property's location, size, and costs.
    """

    class StatusChoices(models.IntegerChoices):
        """Defines the possible status values for a property."""

        AVAILABLE = 1, "Available"
        RENTED = 2, "Rented"
        MAINTENANCE = 3, "Under Maintenance"
        UNAVAILABLE = 4, "Unavailable"

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    area_m2 = models.FloatField()
    current_rent = models.FloatField()
    additional_costs = models.FloatField()
    status = models.IntegerField(
        choices=StatusChoices.choices, default=StatusChoices.AVAILABLE
    )
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE)

    def __str__(self):
        """Return the address and city as the string representation of the property."""
        return f"{self.address}, {self.city}"
