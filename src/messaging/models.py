from django.db import models
from django.utils import timezone
from django.conf import settings

# Get the CustomUser model from settings.AUTH_USER_MODEL
User = settings.AUTH_USER_MODEL


class Message(models.Model):
    """
    Model representing a message in the system.

    A message is sent from one user to another and can be delivered via
    different methods (in-app, email, SMS).
    """

    class DeliveryMethod(models.IntegerChoices):
        """Defines the possible delivery methods for a message."""

        IN_APP = 1, "In-app"
        EMAIL = 2, "Email"
        SMS = 3, "SMS"

    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    delivery_method = models.IntegerField(
        choices=DeliveryMethod.choices, default=DeliveryMethod.IN_APP
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        """Return a string representation of the message."""
        return f"Message from {self.sender} to {self.recipient} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

    def mark_as_read(self):
        """Mark the message as read."""
        self.read = True
        self.save()

    @classmethod
    def get_conversation(cls, user1, user2):
        """
        Get all messages between two users, ordered by timestamp.

        Args:
            user1: The first user in the conversation
            user2: The second user in the conversation

        Returns:
            QuerySet of Message objects
        """
        return cls.objects.filter(
            models.Q(sender=user1, recipient=user2)
            | models.Q(sender=user2, recipient=user1)
        ).order_by("timestamp")

    @classmethod
    def get_unread_count(cls, user):
        """
        Get the count of unread messages for a user.

        Args:
            user: The user to get unread messages for

        Returns:
            Integer count of unread messages
        """
        return cls.objects.filter(recipient=user, read=False).count()
