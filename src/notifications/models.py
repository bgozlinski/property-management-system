import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from properties.models import Property, Unit


"""
This module provides models for notifications and invitations in the system.

It includes models for reminders associated with properties and invitations
for tenants to join the system.
"""


class Reminder(models.Model):
    """
    Model representing a reminder for a unit (apartment/office).

    Reminders are associated with specific units and have a due date.
    They are typically created by landlords to track important tasks or events.
    """

    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="reminders")

    def __str__(self):
        """Return the title as the string representation of the reminder."""
        return self.title


class TenantInvitation(models.Model):
    """
    Model representing an invitation for a tenant to join the system.

    Invitations are sent by landlords to potential tenants. Each invitation
    is associated with a specific property and has an expiration date.
    Invitations can be in various states (pending, accepted, declined, expired).
    """

    class StatusChoices(models.IntegerChoices):
        """Defines the possible status values for a tenant invitation."""

        PENDING = 1, "Pending"
        ACCEPTED = 2, "Accepted"
        DECLINED = 3, "Rejected"
        EXPIRED = 4, "Expired"

    email = models.EmailField()
    property_unit = models.ForeignKey(Property, on_delete=models.CASCADE)
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.IntegerField(
        choices=StatusChoices.choices, default=StatusChoices.PENDING
    )

    @classmethod
    def update_expired_invitations(cls):
        """
        Update the status of all expired invitations from PENDING to EXPIRED.

        This method finds all pending invitations that have passed their
        expiration date and updates their status to EXPIRED.

        Returns:
            int: The number of invitations that were updated.
        """
        now = timezone.now()
        expired_invitations = cls.objects.filter(
            status=cls.StatusChoices.PENDING, expires_at__lt=now
        )
        count = expired_invitations.count()
        expired_invitations.update(status=cls.StatusChoices.EXPIRED)
        return count

    def __str__(self):
        """Return a string representation of the invitation."""
        return f"Zaproszenie dla {self.email} - {self.property_unit}"

    def save(self, *args, **kwargs):
        """
        Save the invitation, setting the expiration date if not provided.

        If no expiration date is provided, it defaults to 7 days from now.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """
        Check if the invitation has expired.

        Returns:
            bool: True if the current time is past the expiration date, False otherwise.
        """
        return timezone.now() > self.expires_at

    @property
    def is_pending(self):
        """
        Check if the invitation is in the pending state.

        Returns:
            bool: True if the invitation status is PENDING, False otherwise.
        """
        return self.status == self.StatusChoices.PENDING
