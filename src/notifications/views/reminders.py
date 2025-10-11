from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import Http404
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from notifications.models import Reminder
from notifications.forms import ReminderForm
from properties.models import Unit
from .mixins import LandlordRequiredMixin


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
        Get the form instance and customize the unit queryset.

        Filters the unit queryset to only show units under buildings owned by the
        current landlord.

        Args:
            form_class: The form class to use, defaults to self.form_class.

        Returns:
            Form: The form instance with filtered unit queryset.
        """
        form = super().get_form(form_class)
        form.fields["unit"].queryset = Unit.objects.filter(
            building__landlord__user=self.request.user
        )
        return form

    def form_valid(self, form):
        """
        Process the valid form and create the reminder.

        Converts the date string to a timezone-aware datetime, verifies that
        the unit belongs to the current landlord, and creates the reminder.

        Args:
            form: The validated reminder form.

        Returns:
            HttpResponse: Redirect to the success URL or back to the form if invalid.
        """
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get("due_date") + " 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
        )

        unit_obj = form.cleaned_data["unit"]
        if unit_obj.building.landlord.user != self.request.user:
            messages.error(
                self.request, "You can only create reminders for your own units."
            )
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, "Reminder created successfully.")
        return response


class ReminderUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    context_object_name = "reminder"
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
        Get the form instance and customize the unit queryset.

        Filters the unit queryset to only show units under buildings owned by the
        current landlord.

        Args:
            form_class: The form class to use, defaults to self.form_class.

        Returns:
            Form: The form instance with filtered unit queryset.
        """
        form = super().get_form(form_class)
        form.fields["unit"].queryset = Unit.objects.filter(
            building__landlord__user=self.request.user
        )
        return form

    def get_object(self, queryset=None):
        """
        Retrieve the reminder and verify ownership.

        Ensures that only the landlord who owns the unit associated with
        the reminder can update it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Reminder: The reminder object if the user is the owner.

        Raises:
            Http404: If the user is not the owner of the unit.
        """
        reminder = super().get_object(queryset)
        if reminder.unit.building.landlord.user != self.request.user:
            raise Http404("Reminder not found")
        return reminder

    def form_valid(self, form):
        """
        Process the valid form and update the reminder.

        Converts the date string to a timezone-aware datetime, verifies that
        the unit belongs to the current landlord, and updates the reminder.

        Args:
            form: The validated reminder form.

        Returns:
            HttpResponse: Redirect to the success URL or back to the form if invalid.
        """
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get("due_date") + " 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
        )

        unit_obj = form.cleaned_data["unit"]
        if unit_obj.building.landlord.user != self.request.user:
            messages.error(
                self.request, "You can only assign reminders to your own units."
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
        Filter reminders to show only those for units under buildings owned by the current landlord.

        Returns:
            QuerySet: Filtered queryset of reminders.
        """
        return Reminder.objects.filter(
            unit__building__landlord__user=self.request.user
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
        form.fields["unit"].queryset = Unit.objects.filter(
            building__landlord__user=self.request.user
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

        Ensures that only the landlord who owns the unit associated with
        the reminder can delete it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Reminder: The reminder object if the user is the owner.

        Raises:
            Http404: If the user is not the owner of the unit.
        """
        reminder = super().get_object(queryset)
        if reminder.unit.building.landlord.user != self.request.user:
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
