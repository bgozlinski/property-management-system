from django.db import models

from leases.models import RentalAgreement


class Payment(models.Model):
    class StatusChoices(models.IntegerChoices):
        PENDING = 1, 'Pending'
        PAID = 2, 'Paid'
        OVERDUE = 3, 'Overdue'
        CANCELLED = 4, 'Cancelled'

    rental_agreement = models.ForeignKey(RentalAgreement, on_delete=models.CASCADE)
    date_due = models.DateField()
    date_paid = models.DateField(null=True, blank=True)
    base_rent = models.FloatField()
    coop_fee = models.FloatField()
    electricity = models.FloatField()
    water = models.FloatField()
    gas = models.FloatField()
    other_fees = models.FloatField()
    total_amount = models.FloatField()
    status = models.IntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    invoice_url = models.URLField(blank=True)

    def __str__(self):
        return f"Payment {self.id} for {self.rental_agreement}"
