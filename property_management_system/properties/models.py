from django.db import models

from users.models import Landlord


class Property(models.Model):
    class StatusChoices(models.IntegerChoices):
        AVAILABLE = 1, 'Available'
        RENTED = 2, 'Rented'
        MAINTENANCE = 3, 'Under Maintenance'
        UNAVAILABLE = 4, 'Unavailable'

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    area_m2 = models.FloatField()
    current_rent = models.FloatField()
    additional_costs = models.FloatField()
    status = models.IntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.AVAILABLE
    )
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.address}, {self.city}"