from django.db import models

from users.models import Tenant
from properties.models import Property


class RentalAgreement(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    base_rent = models.FloatField()
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return f"Agreement for {self.property} - {self.tenant}"