from django.db import models

from users.models import Tenant
from properties.models import Property, Unit


class RentalAgreement(models.Model):
    # Lease period can be open-ended; dates are optional
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Monthly payments agreed in the lease
    base_rent = models.FloatField(help_text="Base monthly payment to the landlord")
    coop_fee = models.FloatField(default=0.0, help_text="Monthly payment for housing cooperative")
    electricity = models.FloatField(default=0.0, help_text="Estimated monthly electricity bill")
    gas = models.FloatField(default=0.0, help_text="Estimated monthly gas bill")
    other_fees = models.FloatField(default=0.0, help_text="Other/extra monthly payments")

    property = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Select the specific unit/apartment for this agreement (optional)",
    )

    def __str__(self) -> str:
        unit_part = f" / {self.unit}" if getattr(self, "unit", None) else ""
        return f"Agreement for {self.property}{unit_part} - {self.tenant}"