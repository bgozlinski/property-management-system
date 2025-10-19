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


class Building(models.Model):
    """Represents a building owned/managed by a landlord."""

    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name="buildings")
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    def __str__(self) -> str:
        return f"{self.name} — {self.address}, {self.city}"


class Unit(models.Model):
    """A unit (apartment/office) located within a building."""

    class UnitType(models.TextChoices):
        APARTMENT = "apartment", "Apartment"
        OFFICE = "office", "Office"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RENTED = "rented", "Rented"
        MAINTENANCE = "maintenance", "Under Maintenance"
        UNAVAILABLE = "unavailable", "Unavailable"

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="units")
    number = models.CharField(max_length=50, help_text="Unit number or name")
    floor = models.IntegerField(null=True, blank=True)
    area_m2 = models.DecimalField(max_digits=8, decimal_places=2)
    unit_type = models.CharField(max_length=20, choices=UnitType.choices, default=UnitType.APARTMENT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    def __str__(self) -> str:
        return f"{self.building.address} / {self.number}, {self.building.city}"


class Equipment(models.Model):
    """Equipment installed in a unit (e.g., fridge, boiler)."""

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="equipment")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    serial_number = models.CharField(max_length=100, blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.unit})"


class Meter(models.Model):
    """Utility meter assigned to a unit."""

    class MeterType(models.TextChoices):
        WATER = "water", "Water"
        ELECTRICITY = "electricity", "Electricity"
        GAS = "gas", "Gas"
        HEAT = "heat", "Heat"

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="meters")
    meter_type = models.CharField(max_length=20, choices=MeterType.choices)
    serial = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.get_meter_type_display()} — {self.serial}"


class MeterReading(models.Model):
    """Reading for a specific meter at a given date."""

    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name="readings")
    date = models.DateField()
    value = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.meter} @ {self.date}: {self.value}"
