import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from properties.models import Property

class Reminder(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    property = models.ForeignKey(Property, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class TenantInvitation(models.Model):
    class StatusChoices(models.IntegerChoices):
        PENDING = 1, 'Pending'
        ACCEPTED = 2, 'Accepted'
        DECLINED = 3, 'Rejected'
        EXPIRED = 4, 'Expired'

    email = models.EmailField()
    property_unit = models.ForeignKey(Property, on_delete=models.CASCADE)
    landlord = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.IntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )

    def __str__(self):
        return f"Zaproszenie dla {self.email} - {self.property_unit}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_pending(self):
        return self.status == self.StatusChoices.PENDING