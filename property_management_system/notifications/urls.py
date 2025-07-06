from django.urls import path
from . import views

urlpatterns = [
    path('send-invitation/', views.send_invitation, name='send_invitation'),
    path('accept-invitation/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
    path('api/reminders/', views.ReminderListCreateAPIView.as_view(), name='api_reminder_list'),
    path('api/reminders/<int:pk>/', views.ReminderDetailAPIView.as_view(), name='api_reminder_detail'),

    path('reminders/add/', views.ReminderCreateView.as_view(), name='add_reminder'),
    path('reminders/<int:pk>/edit/', views.ReminderUpdateView.as_view(), name='edit_reminder'),
    path('reminders/<int:pk>/delete/', views.ReminderDeleteView.as_view(), name='delete_reminder'),
]