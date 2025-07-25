from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.utils import timezone

from .models import CustomUser, Tenant, Landlord
from notifications.models import Reminder
from properties.models import Property
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.views.generic import TemplateView


"""
This module provides views for user registration and profile management.

It includes views for user registration and profile display, handling both
tenant and landlord user types.
"""


class RegisterView(FormView):
    """
    View for user registration.

    Handles the registration form submission, creates the appropriate user type
    (tenant or landlord), and redirects to the dashboard upon successful registration.
    """

    template_name = "sign-up.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        """
        Process the valid form, create the user and associated profile.

        Creates either a Landlord or Tenant profile based on the user's role.

        Args:
            form: The validated registration form.

        Returns:
            HttpResponse: Redirect to the dashboard.
        """
        user = form.save(commit=False)
        if form.cleaned_data.get("is_landlord"):
            user.role = CustomUser.RoleChoices.LANDLORD
        user.save()

        if user.role == CustomUser.RoleChoices.LANDLORD:
            Landlord.objects.create(
                user=user,
                name=f"Landlord {user.email}",
                contact_info="Please update your contact information",
            )
        else:
            Tenant.objects.create(
                user=user,
                name=f"Tenant {user.email}",
                contact_info="Please update your contact information",
            )

        email = form.cleaned_data.get("email")
        messages.success(self.request, f"Account created for {email}!")

        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    View for displaying the user's profile.

    Shows different information based on the user's role (tenant, landlord, or administrator).
    For landlords, it also displays their properties and reminders.
    """

    template_name = "profile.html"

    def get_context_data(self, **kwargs):
        """
        Get the context data for the profile template.

        Retrieves user profile data, role information, and for landlords,
        their properties and reminders.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: Context dictionary with user profile data and role-specific information.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile_data = None
        role_name = "Unknown"
        reminders = []
        landlord_properties = []

        if user.role == CustomUser.RoleChoices.TENANT:
            role_name = "Tenant"
            try:
                profile_data = Tenant.objects.get(user=user)
            except Tenant.DoesNotExist:
                pass
        elif user.role == CustomUser.RoleChoices.LANDLORD:
            role_name = "Landlord"
            try:
                profile_data = Landlord.objects.get(user=user)

                landlord_properties = Property.objects.filter(landlord=profile_data)

                if landlord_properties.exists():
                    reminders = Reminder.objects.filter(
                        property__in=landlord_properties
                    ).order_by("due_date")

            except Landlord.DoesNotExist:
                # Error handling should be implemented here
                pass
        elif user.role == CustomUser.RoleChoices.ADMINISTRATOR:
            role_name = "Administrator"

        context.update(
            {
                "user": user,
                "profile_data": profile_data,
                "role_name": role_name,
                "reminders": reminders,
                "landlord_properties": landlord_properties,
                "current_date": timezone.now(),
            }
        )

        return context
