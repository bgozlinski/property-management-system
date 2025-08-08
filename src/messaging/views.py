from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import get_user_model

from .models import Message
from notifications.models import TenantInvitation

# Get the CustomUser model
User = get_user_model()


class MessageListView(LoginRequiredMixin, ListView):
    """
    View for displaying a list of message conversations for the current user.

    Shows a list of users that the current user has exchanged messages with,
    along with the most recent message and unread message count.
    """

    model = Message
    template_name = "message_list.html"
    context_object_name = "conversations"

    def get_queryset(self):
        """
        Get the list of conversations for the current user.

        Returns a list of dictionaries, each containing:
        - user: The other user in the conversation
        - last_message: The most recent message in the conversation
        - unread_count: The number of unread messages from the other user
        """
        user = self.request.user

        sent_to = (
            Message.objects.filter(sender=user)
            .values_list("recipient", flat=True)
            .distinct()
        )
        received_from = (
            Message.objects.filter(recipient=user)
            .values_list("sender", flat=True)
            .distinct()
        )
        conversation_users = User.objects.filter(
            Q(id__in=sent_to) | Q(id__in=received_from)
        ).distinct()

        conversations = []
        for other_user in conversation_users:
            last_message = (
                Message.objects.filter(
                    Q(sender=user, recipient=other_user)
                    | Q(sender=other_user, recipient=user)
                )
                .order_by("-timestamp")
                .first()
            )

            unread_count = Message.objects.filter(
                sender=other_user, recipient=user, read=False
            ).count()

            conversations.append(
                {
                    "user": other_user,
                    "last_message": last_message,
                    "unread_count": unread_count,
                }
            )

        conversations.sort(
            key=lambda x: x["last_message"].timestamp if x["last_message"] else None,
            reverse=True,
        )

        return conversations


class ConversationView(LoginRequiredMixin, View):
    """
    View for displaying a conversation between the current user and another user.

    Shows all messages between the two users and allows sending new messages.
    """

    template_name = "conversation.html"

    def get(self, request, user_id):
        """
        Display the conversation with the specified user.

        Args:
            request: The HTTP request
            user_id: The ID of the other user in the conversation

        Returns:
            Rendered template with the conversation
        """
        user = request.user
        other_user = get_object_or_404(User, id=user_id)

        messages_list = Message.get_conversation(user, other_user)

        Message.objects.filter(sender=other_user, recipient=user, read=False).update(
            read=True
        )

        return render(
            request,
            self.template_name,
            {"other_user": other_user, "messages": messages_list},
        )

    def post(self, request, user_id):
        """
        Send a new message to the specified user.

        Args:
            request: The HTTP request
            user_id: The ID of the recipient

        Returns:
            Redirect back to the conversation
        """
        user = request.user
        recipient = get_object_or_404(User, id=user_id)
        content = request.POST.get("content", "").strip()

        if content:
            Message.objects.create(
                sender=user,
                recipient=recipient,
                content=content,
                delivery_method=Message.DeliveryMethod.IN_APP,
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message cannot be empty.")

        return redirect("conversation", user_id=user_id)


class NewMessageView(LoginRequiredMixin, View):
    """
    View for composing a new message to a user that the current user hasn't
    messaged before.
    """

    template_name = "new_message.html"

    def get(self, request):
        """
        Display the form for composing a new message.

        Args:
            request: The HTTP request

        Returns:
            Rendered template with the form
        """
        user = request.user

        if user.role == User.RoleChoices.LANDLORD:
            tenant_emails = TenantInvitation.objects.filter(
                landlord=user, status=TenantInvitation.StatusChoices.ACCEPTED
            ).values_list("email", flat=True)

            recipients = User.objects.filter(
                email__in=tenant_emails, role=User.RoleChoices.TENANT
            )
        elif user.role == User.RoleChoices.TENANT:
            landlord_ids = TenantInvitation.objects.filter(
                email=user.email, status=TenantInvitation.StatusChoices.ACCEPTED
            ).values_list("landlord", flat=True)

            recipients = User.objects.filter(id__in=landlord_ids)
        else:
            recipients = User.objects.exclude(id=user.id)

        return render(request, self.template_name, {"recipients": recipients})

    def post(self, request):
        """
        Send a new message to the specified user.

        Args:
            request: The HTTP request

        Returns:
            Redirect to the conversation with the recipient
        """
        user = request.user
        recipient_id = request.POST.get("recipient")
        content = request.POST.get("content", "").strip()

        if not recipient_id:
            messages.error(request, "Please select a recipient.")
            return redirect("new_message")

        if not content:
            messages.error(request, "Message cannot be empty.")
            return redirect("new_message")

        recipient = get_object_or_404(User, id=recipient_id)

        Message.objects.create(
            sender=user,
            recipient=recipient,
            content=content,
            delivery_method=Message.DeliveryMethod.IN_APP,
        )

        messages.success(request, "Message sent successfully.")
        return redirect("conversation", user_id=recipient_id)
