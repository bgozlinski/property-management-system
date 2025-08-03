from django.urls import path
from .views import (
    TenantInvitationListView,
    SendInvitationView,
    AcceptInvitationView,
    ReminderListView,
    ReminderCreateView,
    ReminderUpdateView,
    ReminderDeleteView,
)

urlpatterns = [
    path("invitations/", TenantInvitationListView.as_view(), name="invitation_list"),
    path("send-invitation/", SendInvitationView.as_view(), name="send_invitation"),
    path(
        "accept-invitation/<uuid:token>/",
        AcceptInvitationView.as_view(),
        name="accept_invitation",
    ),
    path("reminders/", ReminderListView.as_view(), name="reminder_list"),
    path("reminders/add/", ReminderCreateView.as_view(), name="add_reminder"),
    path(
        "reminders/<int:pk>/edit/",
        ReminderUpdateView.as_view(),
        name="edit_reminder",
    ),
    path(
        "reminders/<int:pk>/delete/",
        ReminderDeleteView.as_view(),
        name="delete_reminder",
    ),
]
