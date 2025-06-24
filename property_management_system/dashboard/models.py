from django.db import models
from users.models import Landlord, Tenant


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


class RentalAgreement(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    base_rent = models.FloatField()
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self):
        return f"Agreement for {self.property} - {self.tenant}"


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


class MaintenanceRequest(models.Model):
    class StatusChoices(models.IntegerChoices):
        PENDING = 1, 'Pending'
        IN_PROGRESS = 2, 'In Progress'
        COMPLETED = 3, 'Completed'
        CANCELLED = 4, 'Cancelled'

    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.IntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Maintenance Request {self.id} for {self.property}"


class Reminder(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    property = models.ForeignKey(Property, on_delete=models.CASCADE)

    def __str__(self):
        return self.title