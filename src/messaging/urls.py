from django.urls import path
from . import views

urlpatterns = [
    path("", views.MessageListView.as_view(), name="message_list"),
    path("new/", views.NewMessageView.as_view(), name="new_message"),
    path(
        "conversation/<int:user_id>/",
        views.ConversationView.as_view(),
        name="conversation",
    ),
]
