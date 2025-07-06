from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
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
from .serializers import PropertySerializer

# Import the LandlordRequiredMixin from notifications app
from notifications.views import LandlordRequiredMixin


# Existing API views
class PropertyListCreateAPIView(APIView):
    """
    API view to list all properties for a landlord or create a new property
    """

    def get(self, request):
        if request.user.role != CustomUser.RoleChoices.LANDLORD:
            return Response({"error": "Only landlords can view properties"}, status=status.HTTP_403_FORBIDDEN)

        properties = Property.objects.filter(landlord__user=request.user)
        serializer = PropertySerializer(properties, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != CustomUser.RoleChoices.LANDLORD:
            return Response({"error": "Only landlords can add properties"}, status=status.HTTP_403_FORBIDDEN)

        try:
            landlord = request.user.landlord
        except:
            return Response({"error": "Landlord profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['landlord'] = landlord.id

        serializer = PropertySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PropertyDetailAPIView(APIView):
    """
    API view to retrieve, update or delete a property
    """

    def get_object(self, pk, user):
        property = get_object_or_404(Property, pk=pk)
        if property.landlord.user != user and user.role != CustomUser.RoleChoices.ADMINISTRATOR:
            return None
        return property

    def get(self, request, pk):
        property = self.get_object(pk, request.user)
        if not property:
            return Response({"error": "Not found or not authorized"}, status=status.HTTP_404_NOT_FOUND)

        serializer = PropertySerializer(property)
        return Response(serializer.data)

    def put(self, request, pk):
        property = self.get_object(pk, request.user)
        if not property:
            return Response({"error": "Not found or not authorized"}, status=status.HTTP_404_NOT_FOUND)

        serializer = PropertySerializer(property, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        property = self.get_object(pk, request.user)
        if not property:
            return Response({"error": "Not found or not authorized"}, status=status.HTTP_404_NOT_FOUND)

        property.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# New class-based views for properties
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
        # Skip confirmation page and redirect to POST
        return self.post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        # Get the property and check ownership
        property_obj = super().get_object(queryset)
        if property_obj.landlord.user != self.request.user:
            raise Http404("Property not found")
        return property_obj

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Property deleted successfully.")
        return super().delete(request, *args, **kwargs)


# Existing function-based views
@login_required
def property_list(request):
    """View to display and manage properties for a landlord"""
    if request.user.role != CustomUser.RoleChoices.LANDLORD:
        return redirect('dashboard')

    properties = Property.objects.filter(landlord__user=request.user)

    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property = form.save(commit=False)
            property.landlord = request.user.landlord
            property.save()
            return redirect('property_list')
    else:
        form = PropertyForm()

    context = {
        'properties': properties,
        'form': form
    }

    return render(request, 'property_list.html', context)


@login_required
def property_detail(request, pk):
    """View to display and edit a specific property"""
    property = get_object_or_404(Property, pk=pk)

    if property.landlord.user != request.user and request.user.role != CustomUser.RoleChoices.ADMINISTRATOR:
        return redirect('dashboard')

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property)
        if form.is_valid():
            form.save()
            return redirect('property_list')
    else:
        form = PropertyForm(instance=property)

    context = {
        'property': property,
        'form': form
    }

    return render(request, 'property_detail.html', context)