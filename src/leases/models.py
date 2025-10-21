from django.db import models
from users.models import Tenant
from properties.models import Property, Unit

"""
Lease domain models.

This module defines the `RentalAgreement` model, which captures a tenant's rental terms
for a property (and optionally a specific unit). Monetary fields store monthly default
amounts that can be used to pre-fill `Payment` entries (e.g., in the dashboard app).

Key concepts:
- A `RentalAgreement` links a `Tenant` to a `Property`, and optionally to a `Unit` of that property.
- Monetary fields (`base_rent`, `coop_fee`, `electricity`, `gas`, `other_fees`) represent
  expected monthly amounts; they are not computed totals.
- The model's `__str__` provides a human-readable label used in forms/admin.
"""


class RentalAgreement(models.Model):
    """
    A rental/lease agreement between a tenant and a property, optionally narrowed to a unit.

    Fields
    -------
    start_date, end_date : date
        Optional start and end dates of the agreement term.
    base_rent : float
        Base monthly rent paid to the landlord.
    coop_fee : float
        Monthly fee to the housing cooperative.
    electricity : float
        Estimated monthly electricity cost (for budgeting/pre-filling payments).
    gas : float
        Estimated monthly gas cost.
    other_fees : float
        Estimated monthly miscellaneous costs.
    property : ForeignKey[Property]
        The property this agreement pertains to. Optional in case only a unit or tenant
        context is known at creation time.
    tenant : ForeignKey[Tenant]
        The tenant (payer) who is party to the agreement.
    unit : ForeignKey[Unit]
        Optional link to a specific unit/apartment within the property.
    """
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

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
        """
        Return a compact, human-readable label for use in admin and forms.

        Format: always includes the tenant; appends property and/or unit when present, e.g.:
        - "Agreement for John Doe"
        - "Agreement for John Doe Green Street 12 - Apt 5"
        """
        base = f"Agreement for {self.tenant}"
        prop_text = str(self.property) if getattr(self, "property", None) else ""
        unit_text = f"{self.unit}" if getattr(self, "unit", None) else ""
        extra = f" {prop_text} - {unit_text}" if prop_text or unit_text else ""

        return base + extra
