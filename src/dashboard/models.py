from django.db import models

from leases.models import RentalAgreement


class Payment(models.Model):
    """Represents a single monthly payment tied to a rental agreement.

    Includes computed tax fields used for Polish landlords, where the
    effective tax rate and amount are derived from the base_rent and
    year-to-date thresholds.
    """
    class StatusChoices(models.IntegerChoices):
        PENDING = 1, 'Pending'
        PAID = 2, 'Paid'
        OVERDUE = 3, 'Overdue'
        CANCELLED = 4, 'Cancelled'

    rental_agreement = models.ForeignKey(RentalAgreement, on_delete=models.SET_NULL, null=True, blank=True)
    date_due = models.DateField()
    date_paid = models.DateField(null=True, blank=True)
    base_rent = models.FloatField()
    coop_fee = models.FloatField()
    electricity = models.FloatField()
    water = models.FloatField()
    gas = models.FloatField()
    other_fees = models.FloatField()
    tax_rate = models.FloatField(default=0.0, help_text="Effective tax rate for this month (fraction, e.g., 0.085 for 8.5%)")
    tax_amount = models.FloatField(default=0.0, help_text="Computed tax for this month based on base_rent")
    total_amount = models.FloatField()
    status = models.IntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    invoice_url = models.URLField(blank=True)

    def __str__(self):
        return f"Payment {self.id} for {self.rental_agreement}"

    @property
    def tax_rate_percent(self) -> float:
        """Return tax rate as percentage value for display (e.g., 8.5)."""
        try:
            return float(self.tax_rate or 0.0) * 100.0
        except Exception:
            return 0.0

    @property
    def tax_rate_with_sign(self) -> str:
        """Formatted percentage string (e.g., "8.50%") for display in templates without filters."""
        try:
            return f"{float(self.tax_rate or 0.0) * 100.0:.2f}%"
        except Exception:
            return "0.00%"

    @property
    def tax_rate_display(self) -> str:
        """Return formatted tax percentage without the percent sign (e.g., "8.50")."""
        try:
            return f"{float(self.tax_rate or 0.0) * 100.0:.2f}"
        except Exception:
            return "0.00"
