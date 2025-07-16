from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import Http404
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import Property
from users.models import CustomUser
from .forms import PropertyForm
from notifications.views import LandlordRequiredMixin


class PropertyCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'add_property.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        # Set the landlord to the current user's landlord profile
        form.instance.landlord = self.request.user.landlord
        response = super().form_valid(form)
        messages.success(self.request, "Property created successfully.")
        return response


class PropertyUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'property_detail.html'  # Reuse existing template
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        # Get the property and check ownership
        property_obj = super().get_object(queryset)
        if property_obj.landlord.user != self.request.user:
            raise Http404("Property not found")
        return property_obj

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Property updated successfully.")
        return response


class PropertyDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    model = Property
    success_url = reverse_lazy('profile')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        property_obj = super().get_object(queryset)
        if property_obj.landlord.user != self.request.user:
            raise Http404("Property not found")
        return property_obj

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Property deleted successfully.")
        return super().delete(request, *args, **kwargs)

class PropertyListView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'property_list.html'
    success_url = reverse_lazy('property_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['properties'] = Property.objects.filter(landlord__user=self.request.user)
        return context

    def form_valid(self, form):
        property = form.save(commit=False)
        property.landlord = self.request.user.landlord
        property.save()
        return redirect('property_list')

class PropertyDetailView(LoginRequiredMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'property_detail.html'
    success_url = reverse_lazy('property_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.landlord.user != self.request.user and self.request.user.role != CustomUser.RoleChoices.ADMINISTRATOR:
            raise Http404("Property not found")
        return obj
