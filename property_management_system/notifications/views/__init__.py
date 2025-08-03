"""
This package provides views for notifications and invitations in the system.

It includes views for sending and accepting tenant invitations, as well as
creating, updating, and deleting reminders for properties.
"""

# Import and expose the LandlordRequiredMixin
from .mixins import LandlordRequiredMixin

# Import and expose all reminder-related views
from .reminders import (
    ReminderCreateView,
    ReminderUpdateView,
    ReminderListView,
    ReminderDeleteView,
)

# Import and expose all invitation-related views
from .invitations import (
    SendInvitationView,
    TenantInvitationListView,
    AcceptInvitationView,
)

# Define __all__ to explicitly specify what is exported from this package
__all__ = [
    "LandlordRequiredMixin",
    "ReminderCreateView",
    "ReminderUpdateView",
    "ReminderListView",
    "ReminderDeleteView",
    "SendInvitationView",
    "TenantInvitationListView",
    "AcceptInvitationView",
]
