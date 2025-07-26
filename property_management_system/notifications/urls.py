from django.urls import path
from . import views

urlpatterns = [
    # Invitation URLs
    path(
        "invitations/", views.TenantInvitationListView.as_view(), name="invitation_list"
    ),
    path(
        "send-invitation/", views.SendInvitationView.as_view(), name="send_invitation"
    ),
    path(
        "accept-invitation/<uuid:token>/",
        views.AcceptInvitationView.as_view(),
        name="accept_invitation",
    ),
    # Reminder URLs
    path("reminders/", views.ReminderListView.as_view(), name="reminder_list"),
    path("reminders/add/", views.ReminderCreateView.as_view(), name="add_reminder"),
    path(
        "reminders/<int:pk>/edit/",
        views.ReminderUpdateView.as_view(),
        name="edit_reminder",
    ),
    path(
        "reminders/<int:pk>/delete/",
        views.ReminderDeleteView.as_view(),
        name="delete_reminder",
    ),
]
