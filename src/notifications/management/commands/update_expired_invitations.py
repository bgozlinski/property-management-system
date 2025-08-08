from django.core.management.base import BaseCommand
from notifications.models import TenantInvitation


class Command(BaseCommand):
    """
    Management command to update the status of expired tenant invitations.

    This command finds all pending invitations that have passed their
    expiration date and updates their status to EXPIRED.
    """

    help = "Updates the status of expired tenant invitations from PENDING to EXPIRED"

    def handle(self, *args, **options):
        """
        Execute the command to update expired invitations.

        Args:
            *args: Additional positional arguments.
            **options: Additional keyword arguments.

        Returns:
            None
        """
        count = TenantInvitation.update_expired_invitations()

        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {count} expired invitation(s)"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("No expired invitations found"))
