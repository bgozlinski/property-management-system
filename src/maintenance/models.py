from django.db import models

from properties.models import Property
from users.models import Tenant

class MaintenanceRequest(models.Model):
    class StatusChoices(models.IntegerChoices):
        PENDING = 1, 'Pending'
        IN_PROGRESS = 2, 'In Progress'
        COMPLETED = 3, 'Completed'
        CANCELLED = 4, 'Cancelled'

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='maintenance_requests')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='maintenance_requests')
    description = models.TextField(help_text="Describe the maintenance you want to perform.")
    status = models.IntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        help_text="Current status of the maintenance request."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"Maintenance Request {self.id} for {self.property}"
