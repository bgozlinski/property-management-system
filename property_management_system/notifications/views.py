from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.conf import settings
from django.http import Http404
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView, FormView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Reminder, TenantInvitation
from .forms import TenantInvitationForm, ReminderForm
from users.models import CustomUser, Tenant
from properties.models import Property

from django.utils.translation import gettext as _


"""
This module provides views for notifications and invitations in the system.

It includes views for sending and accepting tenant invitations, as well as
creating, updating, and deleting reminders for properties.
"""


class LandlordRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure only landlords can access the view.

    This mixin checks if the current user is authenticated and has the
    LANDLORD role before allowing access to the view.
    """

    def test_func(self):
        """
        Test if the current user is a landlord.

        Returns:
            bool: True if the user is authenticated and has the LANDLORD role,
                 False otherwise.
        """
        return (
            self.request.user.is_authenticated
            and self.request.user.role == CustomUser.RoleChoices.LANDLORD
        )


class SendInvitationView(LoginRequiredMixin, LandlordRequiredMixin, FormView):
    """
    View for landlords to send invitations to tenants.

    This view allows landlords to invite tenants to join the system by sending
    them an email with a unique invitation link. Only authenticated landlords
    can access this view.
    """

    template_name = "send_invitation.html"
    form_class = TenantInvitationForm
    success_url = reverse_lazy("invitation_list")

    def get_form_kwargs(self):
        """
        Add the current user as a landlord to the form kwargs.

        This ensures that the form only shows properties owned by the current landlord.

        Returns:
            dict: The form kwargs with the landlord added.
        """
        kwargs = super().get_form_kwargs()
        kwargs["landlord"] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests, including  tation cancellation.

        If the request includes a cancel_invitation parameter, the invitation
        is deleted. Otherwise, the form is processed normally.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect to the success URL.
        """
        # Check if this is a cancellation request
        if "cancel_invitation" in request.POST and request.POST["cancel_invitation"]:
            invitation_id = request.POST["cancel_invitation"]
            try:
                # Allow deleting for PENDING, EXPIRED, and ACCEPTED invitations
                invitation = TenantInvitation.objects.get(
                    id=invitation_id,
                    landlord=request.user,
                    status__in=[
                        TenantInvitation.StatusChoices.PENDING,
                        TenantInvitation.StatusChoices.EXPIRED,
                        TenantInvitation.StatusChoices.ACCEPTED,
                    ],
                )
                invitation.delete()
                messages.success(request, _("Invitation deleted successfully!"))
                return redirect(self.success_url)
            except TenantInvitation.DoesNotExist:
                messages.error(request, _("Invitation not found or cannot be deleted."))
                return redirect(self.success_url)

        # Handle resend request
        if "resend" in request.GET:
            invitation_id = request.GET["resend"]
            try:
                # Allow resending for both PENDING and EXPIRED invitations
                invitation = TenantInvitation.objects.get(
                    id=invitation_id,
                    landlord=request.user,
                    status__in=[
                        TenantInvitation.StatusChoices.PENDING,
                        TenantInvitation.StatusChoices.EXPIRED,
                    ],
                )

                # If the invitation was expired, update its status to PENDING and set a new expiration date
                if invitation.status == TenantInvitation.StatusChoices.EXPIRED:
                    invitation.status = TenantInvitation.StatusChoices.PENDING
                    invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
                    invitation.save()

                # Update the created_at field to reflect the new sent date
                # Since created_at has auto_now_add=True, we need to update it directly in the database
                now = timezone.now()
                TenantInvitation.objects.filter(id=invitation.id).update(created_at=now)
                # Refresh the invitation object to get the updated created_at value
                invitation.refresh_from_db()

                invitation_url = self.request.build_absolute_uri(
                    reverse("accept_invitation", args=[invitation.token])
                )

                send_mail(
                    _("Invitation to join Property Management System"),
                    _(
                        "You have been invited to join the Property Management System. "
                        "Click the link to accept: {}"
                    ).format(invitation_url),
                    settings.DEFAULT_FROM_EMAIL,
                    [invitation.email],
                    fail_silently=False,
                )

                messages.success(request, _("Invitation resent successfully!"))
                return redirect(self.success_url)
            except TenantInvitation.DoesNotExist:
                messages.error(request, _("Invitation not found or cannot be resent."))
                return redirect(self.success_url)

        # Normal form processing
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Process the valid form, create the invitation, and send the email.

        Creates a tenant invitation associated with the current landlord and
        sends an email to the tenant with a link to accept the invitation.

        Args:
            form: The validated invitation form.

        Returns:
            HttpResponse: Redirect to the success URL.
        """
        invitation = form.save(commit=False)
        invitation.landlord = self.request.user
        invitation.save()

        invitation_url = self.request.build_absolute_uri(
            reverse("accept_invitation", args=[invitation.token])
        )

        send_mail(
            _("Invitation to join Property Management System"),
            _(
                "You have been invited to join the Property Management System. "
                "Click the link to accept: {}"
            ).format(invitation_url),
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email],
            fail_silently=False,
        )

        messages.success(self.request, _("Invitation sent successfully!"))
        return super().form_valid(form)


class TenantInvitationListView(LoginRequiredMixin, LandlordRequiredMixin, ListView):
    """
    View for listing tenant invitations.

    This view displays a list of invitations sent by the current landlord.
    It also provides a form for creating new invitations.
    Only authenticated landlords can access this view.

    Before displaying the invitations, it updates the status of any expired
    invitations from PENDING to EXPIRED.
    """

    model = TenantInvitation
    template_name = "invitation_list.html"
    context_object_name = "invitations"

    def get_queryset(self):
        """
        Update expired invitations and filter to show only those sent by the current landlord.

        First, it updates any pending invitations that have expired.
        Then, it returns a queryset of all invitations sent by the current landlord.

        Returns:
            QuerySet: Filtered queryset of invitations.
        """
        # Update expired invitations
        TenantInvitation.update_expired_invitations()  # TODO celery in the future.

        # Return invitations for the current landlord
        return TenantInvitation.objects.filter(landlord=self.request.user).order_by(
            "-created_at"
        )

    def get_context_data(self, **kwargs):
        """
        Add the invitation form to the context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: Context dictionary with the invitation form.
        """
        context = super().get_context_data(**kwargs)
        form = TenantInvitationForm(landlord=self.request.user)
        context["form"] = form
        return context


class AcceptInvitationView(View):
    """
    View for accepting tenant invitations.

    This view handles both GET and POST requests for accepting invitations.
    GET requests display the invitation acceptance form, while POST requests
    process the form submission and create or update the user account.

    Before processing the invitation, it updates the status of any expired
    invitations from PENDING to EXPIRED.
    """

    template_name = "accept_invitation.html"

    def get(self, request, token):
        """
        Handle GET requests to display the invitation acceptance form.

        First, it updates any pending invitations that have expired.
        Then, it retrieves the invitation by token and displays the acceptance form
        if the invitation is valid and not expired.

        Args:
            request: The HTTP request.
            token: The invitation token.

        Returns:
            HttpResponse: The rendered template or a redirect to login if expired.
        """
        # Update expired invitations
        TenantInvitation.update_expired_invitations()

        invitation = get_object_or_404(
            TenantInvitation, token=token, status=TenantInvitation.StatusChoices.PENDING
        )

        if invitation.is_expired:
            messages.error(request, _("This invitation has expired."))
            return redirect("login")

        context = {"invitation": invitation}
        return render(request, self.template_name, context)

    def post(self, request, token):
        """
        Handle POST requests to process the invitation acceptance.

        First, it updates any pending invitations that have expired.
        Then, it retrieves the invitation by token, creates or updates the user account,
        and marks the invitation as accepted.

        Args:
            request: The HTTP request.
            token: The invitation token.

        Returns:
            HttpResponse: Redirect to login page after successful processing.
        """
        # Update expired invitations
        TenantInvitation.update_expired_invitations()

        invitation = get_object_or_404(
            TenantInvitation, token=token, status=TenantInvitation.StatusChoices.PENDING
        )

        if invitation.is_expired:
            messages.error(request, _("This invitation has expired."))
            return redirect("login")

        try:
            user = CustomUser.objects.get(email=invitation.email)
            if user.role != CustomUser.RoleChoices.TENANT:
                user.role = CustomUser.RoleChoices.TENANT
                user.save()
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(
                email=invitation.email,
                password=request.POST.get("password"),
                role=CustomUser.RoleChoices.TENANT,
            )

        # Create a Tenant profile for the user if one doesn't exist
        Tenant.objects.get_or_create(
            user=user,
            defaults={
                "name": invitation.email.split("@")[0],
                "contact_info": invitation.email,
            },
        )

        invitation.status = TenantInvitation.StatusChoices.ACCEPTED
        invitation.save()

        messages.success(
            request, _("Invitation accepted successfully! You can now log in.")
        )
        return redirect("login")


class ReminderCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    """
    View for creating a new reminder.

    This view allows landlords to create reminders for their properties.
    Only authenticated landlords can access this view.
    """

    model = Reminder
    form_class = ReminderForm
    template_name = "add_reminder.html"
    success_url = reverse_lazy("reminder_list")

    def get_form(self, form_class=None):
        """
        Get the form instance and customize the property queryset.

        Filters the property queryset to only show properties owned by the
        current landlord.

        Args:
            form_class: The form class to use, defaults to self.form_class.

        Returns:
            Form: The form instance with filtered property queryset.
        """
        form = super().get_form(form_class)
        form.fields["property"].queryset = Property.objects.filter(
            landlord__user=self.request.user
        )
        return form

    def form_valid(self, form):
        """
        Process the valid form and create the reminder.

        Converts the date string to a timezone-aware datetime, verifies that
        the property belongs to the current landlord, and creates the reminder.

        Args:
            form: The validated reminder form.

        Returns:
            HttpResponse: Redirect to the success URL or back to the form if invalid.
        """
        # Convert the date string to a timezone-aware datetime
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get("due_date") + " 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
        )

        # Verify that the property belongs to the current landlord
        property_obj = form.cleaned_data["property"]
        if property_obj.landlord.user != self.request.user:
            messages.error(
                self.request, "You can only create reminders for your own properties."
            )
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, "Reminder created successfully.")
        return response


class ReminderUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    """
    View for updating an existing reminder.

    This view allows landlords to update reminders for their properties.
    Only authenticated landlords can access this view, and they can only
    update reminders for properties they own.
    """

    model = Reminder
    form_class = ReminderForm
    template_name = "edit_reminder.html"
    success_url = reverse_lazy("reminder_list")

    def get_form(self, form_class=None):
        """
        Get the form instance and customize the property queryset.

        Filters the property queryset to only show properties owned by the
        current landlord.

        Args:
            form_class: The form class to use, defaults to self.form_class.

        Returns:
            Form: The form instance with filtered property queryset.
        """
        form = super().get_form(form_class)
        form.fields["property"].queryset = Property.objects.filter(
            landlord__user=self.request.user
        )
        return form

    def get_object(self, queryset=None):
        """
        Retrieve the reminder and verify ownership.

        Ensures that only the landlord who owns the property associated with
        the reminder can update it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Reminder: The reminder object if the user is the owner.

        Raises:
            Http404: If the user is not the owner of the property.
        """
        reminder = super().get_object(queryset)
        if reminder.property.landlord.user != self.request.user:
            raise Http404("Reminder not found")
        return reminder

    def form_valid(self, form):
        """
        Process the valid form and update the reminder.

        Converts the date string to a timezone-aware datetime, verifies that
        the property belongs to the current landlord, and updates the reminder.

        Args:
            form: The validated reminder form.

        Returns:
            HttpResponse: Redirect to the success URL or back to the form if invalid.
        """
        # Convert the date string to a timezone-aware datetime
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get("due_date") + " 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
        )

        # Verify that the property belongs to the current landlord
        property_obj = form.cleaned_data["property"]
        if property_obj.landlord.user != self.request.user:
            messages.error(
                self.request, "You can only assign reminders to your own properties."
            )
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, "Reminder updated successfully.")
        return response


class ReminderListView(LoginRequiredMixin, LandlordRequiredMixin, ListView):
    """
    View for listing reminders.

    This view displays a list of reminders for properties owned by the current landlord.
    It also provides a form for creating new reminders.
    Only authenticated landlords can access this view.
    """

    model = Reminder
    template_name = "reminder_list.html"
    context_object_name = "reminders"

    def get_queryset(self):
        """
        Filter reminders to show only those for properties owned by the current landlord.

        Returns:
            QuerySet: Filtered queryset of reminders.
        """
        return Reminder.objects.filter(
            property__landlord__user=self.request.user
        ).order_by("due_date")

    def get_context_data(self, **kwargs):
        """
        Add the reminder form to the context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: Context dictionary with the reminder form.
        """
        context = super().get_context_data(**kwargs)
        form = ReminderForm()
        form.fields["property"].queryset = Property.objects.filter(
            landlord__user=self.request.user
        )
        context["form"] = form
        return context


class ReminderDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    """
    View for deleting an existing reminder.

    This view allows landlords to delete reminders for their properties.
    Only authenticated landlords can access this view, and they can only
    delete reminders for properties they own.
    """

    model = Reminder
    success_url = reverse_lazy("reminder_list")

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests by redirecting to POST.

        This prevents showing a confirmation page and directly processes
        the deletion when accessed via GET.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: The result of the POST method.
        """
        return self.post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """
        Retrieve the reminder and verify ownership.

        Ensures that only the landlord who owns the property associated with
        the reminder can delete it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Reminder: The reminder object if the user is the owner.

        Raises:
            Http404: If the user is not the owner of the property.
        """
        reminder = super().get_object(queryset)
        if reminder.property.landlord.user != self.request.user:
            raise Http404("Reminder not found")
        return reminder

    def delete(self, request, *args, **kwargs):
        """
        Delete the reminder and show a success message.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect to the success URL with a success message.
        """
        messages.success(request, "Reminder deleted successfully.")
        return super().delete(request, *args, **kwargs)
