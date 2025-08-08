"""
This module provides views for notifications and invitations in the system.

It includes views for sending and accepting tenant invitations, as well as
creating, updating, and deleting reminders for properties.

Note: This file is maintained for backward compatibility.
The actual implementation has been moved to the views package.
"""

from .views.mixins import LandlordRequiredMixin
from .views.reminders import (
    ReminderCreateView,
    ReminderUpdateView,
    ReminderListView,
    ReminderDeleteView,
)
from .views.invitations import (
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
