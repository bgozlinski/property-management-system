from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import Http404
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import Property
from users.models import CustomUser
from .forms import PropertyForm
from notifications.views import LandlordRequiredMixin


"""
This module provides views for property management in the system.

It includes views for creating, updating, deleting, listing, and viewing
property details, with appropriate access controls for landlords.
"""


class PropertyCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    """
    View for creating a new property.

    Only landlords can create properties. The property is automatically
    associated with the current user's landlord profile.
    """

    model = Property
    form_class = PropertyForm
    template_name = "add_property.html"
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        """
        Process the valid form and associate the property with the landlord.

        Args:
            form: The validated property form.

        Returns:
            HttpResponse: Redirect to the success URL with a success message.
        """
        form.instance.landlord = self.request.user.landlord
        response = super().form_valid(form)
        messages.success(self.request, "Property created successfully.")
        return response


class PropertyUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    """
    View for updating an existing property.

    Only landlords can update their own properties. Access is restricted
    to the property owner.
    """

    model = Property
    form_class = PropertyForm
    template_name = "property_detail.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        """
        Retrieve the property and verify ownership.

        Ensures that only the landlord who owns the property can update it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Property: The property object if the user is the owner.

        Raises:
            Http404: If the user is not the owner of the property.
        """
        property_obj = super().get_object(queryset)
        if property_obj.landlord.user != self.request.user:
            raise Http404("Property not found")
        return property_obj

    def form_valid(self, form):
        """
        Process the valid form and save the updated property.

        Args:
            form: The validated property form.

        Returns:
            HttpResponse: Redirect to the success URL with a success message.
        """
        response = super().form_valid(form)
        messages.success(self.request, "Property updated successfully.")
        return response


class PropertyDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    """
    View for deleting an existing property.

    Only landlords can delete their own properties. Access is restricted
    to the property owner.
    """

    model = Property
    success_url = reverse_lazy("profile")

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
        Retrieve the property and verify ownership.

        Ensures that only the landlord who owns the property can delete it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Property: The property object if the user is the owner.

        Raises:
            Http404: If the user is not the owner of the property.
        """
        property_obj = super().get_object(queryset)
        if property_obj.landlord.user != self.request.user:
            raise Http404("Property not found")
        return property_obj

    def delete(self, request, *args, **kwargs):
        """
        Delete the property and show a success message.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect to the success URL with a success message.
        """
        messages.success(request, "Property deleted successfully.")
        return super().delete(request, *args, **kwargs)


class PropertyListView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    """
    View for listing properties and creating new ones.

    This view serves a dual purpose:
    1. It displays a list of properties owned by the current landlord
    2. It provides a form for creating new properties

    Only landlords can access this view.
    """

    model = Property
    form_class = PropertyForm
    template_name = "property_list.html"
    success_url = reverse_lazy("property_list")

    def get_context_data(self, **kwargs):
        """
        Add the list of properties owned by the current landlord to the context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: Context dictionary with the landlord's properties.
        """
        context = super().get_context_data(**kwargs)
        context["properties"] = Property.objects.filter(
            landlord__user=self.request.user
        )
        return context

    def form_valid(self, form):
        """
        Process the valid form and associate the property with the landlord.

        Args:
            form: The validated property form.

        Returns:
            HttpResponse: Redirect to the property list.
        """
        property = form.save(commit=False)
        property.landlord = self.request.user.landlord
        property.save()
        return redirect("property_list")


class PropertyDetailView(LoginRequiredMixin, UpdateView):
    """
    View for displaying and updating property details.

    This view allows landlords to view and update their own properties.
    Administrators can also view and update any property.
    """

    model = Property
    form_class = PropertyForm
    template_name = "property_detail.html"
    success_url = reverse_lazy("property_list")

    def get_object(self, queryset=None):
        """
        Retrieve the property and verify access permissions.

        Ensures that only the landlord who owns the property or an administrator
        can view and update it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Property: The property object if the user has permission.

        Raises:
            Http404: If the user doesn't have permission to access the property.
        """
        obj = super().get_object(queryset)
        if (
            obj.landlord.user != self.request.user
            and self.request.user.role != CustomUser.RoleChoices.ADMINISTRATOR
        ):
            raise Http404("Property not found")
        return obj
