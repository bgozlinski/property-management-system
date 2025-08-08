from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.conf import settings
from django.views import View
from django.views.generic import FormView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from notifications.models import TenantInvitation
from notifications.forms import TenantInvitationForm
from users.models import CustomUser, Tenant
from .mixins import LandlordRequiredMixin

from django.utils.translation import gettext as _


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

                if invitation.status == TenantInvitation.StatusChoices.EXPIRED:
                    invitation.status = TenantInvitation.StatusChoices.PENDING
                    invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
                    invitation.save()

                now = timezone.now()
                TenantInvitation.objects.filter(id=invitation.id).update(created_at=now)
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
