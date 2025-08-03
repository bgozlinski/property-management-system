"""
This package provides views for notifications and invitations in the system.

It includes views for sending and accepting tenant invitations, as well as
creating, updating, and deleting reminders for properties.

Note: This package is the actual implementation of the views.
The top-level views.py file imports from this package and re-exports
the same classes for backward compatibility with existing code.
"""

from .mixins import LandlordRequiredMixin
from .reminders import (
    ReminderCreateView,
    ReminderUpdateView,
    ReminderListView,
    ReminderDeleteView,
)
from .invitations import (
    SendInvitationView,
    TenantInvitationListView,
    AcceptInvitationView,
)

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
