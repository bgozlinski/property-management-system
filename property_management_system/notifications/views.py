from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.conf import settings
from django.http import Http404
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Reminder, TenantInvitation
from .forms import TenantInvitationForm, ReminderForm
from .serializers import ReminderSerializer
from users.models import CustomUser
from properties.models import Property

from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST


# Existing function-based views for invitations
@login_required
def send_invitation(request):
    # Existing code...
    # (Keep the existing implementation)
    if request.user.role != CustomUser.RoleChoices.LANDLORD:
        messages.error(request, "Only Landlords can send invitations.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = TenantInvitationForm(request.POST, landlord=request.user)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.landlord = request.user
            invitation.save()

            invitation_url = request.build_absolute_uri(
                reverse('accept_invitation', kwargs={'token': invitation.token})
            )

            subject = _(f"Zaproszenie do wynajmu nieruchomości: {invitation.property_unit}")
            message = f"""
            Witaj!

            Zostałeś zaproszony przez {request.user.email} do wynajmu nieruchomości:
            {invitation.property_unit}

            Aby zaakceptować zaproszenie, kliknij w poniższy link:
            {invitation_url}

            Link jest ważny do: {invitation.expires_at.strftime('%d-%m-%Y %H:%M')}

            Pozdrawiamy,
            System zarządzania nieruchomościami
            """

            # Send email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@example.com',
                [invitation.email],
                fail_silently=False,
            )

            messages.success(request, f"Zaproszenie zostało wysłane na adres {invitation.email}.")
            return redirect('dashboard')
    else:
        form = TenantInvitationForm(landlord=request.user)

    return render(request, 'send_invitation.html', {'form': form})


def accept_invitation(request, token):
    # Existing code...
    # (Keep the existing implementation)
    invitation = get_object_or_404(TenantInvitation, token=token)

    if invitation.is_expired:
        invitation.status = TenantInvitation.StatusChoices.EXPIRED
        invitation.save()
        messages.error(request, "This invitation has expired.")
        return redirect('login')

    if not invitation.is_pending:
        messages.error(request, "This invitation has already been accepted or declined. Please login to continue.")
        return redirect('login')

    if request.user.is_authenticated:
        if request.user.email == invitation.email:
            invitation.status = TenantInvitation.StatusChoices.ACCEPTED
            invitation.save()

            messages.success(request,
                             f"Invitation fo property {invitation.property_unit} has been accepted.")
            return redirect('dashboard')
        else:
            messages.error(request, "This invitation is not for you. Please login to continue.")
            return redirect('dashboard')

    request.session['invitation_token'] = str(invitation.token)
    messages.info(request, "To accept this invitation, please login with your email address.")

    if CustomUser.objects.filter(email=invitation.email).exists():
        return redirect('login')

    return redirect('register')


# Existing API views
class ReminderListCreateAPIView(APIView):
    """
    API view to list all reminders for a landlord's properties or create a new reminder
    """

    def get(self, request):
        if request.user.role != CustomUser.RoleChoices.LANDLORD:
            return Response({"error": "Only landlords can view reminders"}, status=status.HTTP_403_FORBIDDEN)

        landlord_properties = Property.objects.filter(landlord__user=request.user)

        reminders = Reminder.objects.filter(property__in=landlord_properties).order_by('due_date')

        serializer = ReminderSerializer(reminders, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != CustomUser.RoleChoices.LANDLORD:
            return Response({"error": "Only landlords can add reminders"}, status=status.HTTP_403_FORBIDDEN)

        property_id = request.data.get('property')
        if property_id:
            try:
                property_obj = Property.objects.get(id=property_id)
                if property_obj.landlord.user != request.user:
                    return Response(
                        {"error": "You can only create reminders for your own properties"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Property.DoesNotExist:
                return Response({"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReminderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReminderDetailAPIView(APIView):
    """
    API view to retrieve, update or delete a reminder
    """

    def get_object(self, pk, user):
        reminder = get_object_or_404(Reminder, pk=pk)

        if reminder.property.landlord.user != user and user.role != CustomUser.RoleChoices.ADMINISTRATOR:
            return None
        return reminder

    def get(self, request, pk):
        reminder = self.get_object(pk, request.user)
        if not reminder:
            return Response({"error": "Not found or not authorized"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReminderSerializer(reminder)
        return Response(serializer.data)

    def put(self, request, pk):
        reminder = self.get_object(pk, request.user)
        if not reminder:
            return Response({"error": "Not found or not authorized"}, status=status.HTTP_404_NOT_FOUND)

        property_id = request.data.get('property')
        if property_id and int(property_id) != reminder.property.id:
            try:
                property_obj = Property.objects.get(id=property_id)
                if property_obj.landlord.user != request.user:
                    return Response(
                        {"error": "You can only assign reminders to your own properties"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Property.DoesNotExist:
                return Response({"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReminderSerializer(reminder, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        reminder = self.get_object(pk, request.user)
        if not reminder:
            return Response({"error": "Not found or not authorized"}, status=status.HTTP_404_NOT_FOUND)

        reminder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Mixin for landlord permission check
class LandlordRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only landlords can access the view"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == CustomUser.RoleChoices.LANDLORD


# New class-based views for reminders
class ReminderCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    model = Reminder
    form_class = ReminderForm
    template_name = 'add_reminder.html'
    success_url = reverse_lazy('profile')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter properties to show only those owned by the current landlord
        form.fields['property'].queryset = Property.objects.filter(landlord__user=self.request.user)
        return form

    def form_valid(self, form):
        # Format the date for API
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get('due_date') + ' 00:00:00',
                '%Y-%m-%d %H:%M:%S'
            )
        )

        # Verify property ownership
        property_obj = form.cleaned_data['property']
        if property_obj.landlord.user != self.request.user:
            messages.error(self.request, "You can only create reminders for your own properties.")
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, "Reminder created successfully.")
        return response


class ReminderUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    model = Reminder
    form_class = ReminderForm
    template_name = 'edit_reminder.html'
    success_url = reverse_lazy('profile')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter properties to show only those owned by the current landlord
        form.fields['property'].queryset = Property.objects.filter(landlord__user=self.request.user)
        return form

    def get_object(self, queryset=None):
        # Get the reminder and check ownership
        reminder = super().get_object(queryset)
        if reminder.property.landlord.user != self.request.user:
            raise Http404("Reminder not found")
        return reminder

    def form_valid(self, form):
        # Format the date for API
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get('due_date') + ' 00:00:00',
                '%Y-%m-%d %H:%M:%S'
            )
        )

        # Verify property ownership
        property_obj = form.cleaned_data['property']
        if property_obj.landlord.user != self.request.user:
            messages.error(self.request, "You can only assign reminders to your own properties.")
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, "Reminder updated successfully.")
        return response


class ReminderDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    model = Reminder
    success_url = reverse_lazy('profile')

    def get(self, request, *args, **kwargs):
        # Skip confirmation page and redirect to POST
        return self.post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        # Get the reminder and check ownership
        reminder = super().get_object(queryset)
        if reminder.property.landlord.user != self.request.user:
            raise Http404("Reminder not found")
        return reminder

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Reminder deleted successfully.")
        return super().delete(request, *args, **kwargs)


# Keep the existing function-based views for backward compatibility
@login_required
def add_reminder(request):
    """View to add a new reminder using the existing ReminderListCreateAPIView"""
    if request.method == 'POST':
        # Create a data dictionary from the form data
        data = {
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'property': request.POST.get('property'),
            'due_date': request.POST.get('due_date') + 'T00:00:00Z',  # Format date for API
        }

        # Create a request object for the APIView
        api_request = request._request
        api_request.data = data

        # Use the existing APIView to handle the request
        view = ReminderListCreateAPIView()
        response = view.post(api_request)

        # Handle the response
        if response.status_code == status.HTTP_201_CREATED:
            messages.success(request, "Reminder created successfully.")
        else:
            for field, errors in response.data.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    return redirect('profile')


@login_required
def edit_reminder(request, pk):
    """View to edit an existing reminder using the existing ReminderDetailAPIView"""
    # Get the reminder using the APIView's get_object method
    detail_view = ReminderDetailAPIView()
    reminder = detail_view.get_object(pk, request.user)

    if not reminder:
        messages.error(request, "Reminder not found or you don't have permission to edit it.")
        return redirect('profile')

    if request.method == 'POST':
        # Create a data dictionary from the form data
        data = {
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'property': request.POST.get('property'),
            'due_date': request.POST.get('due_date') + 'T00:00:00Z',  # Format date for API
        }

        # Create a request object for the APIView
        api_request = request._request
        api_request.data = data

        # Use the existing APIView to handle the request
        response = detail_view.put(api_request, pk)

        # Handle the response
        if response.status_code == status.HTTP_200_OK:
            messages.success(request, "Reminder updated successfully.")
            return redirect('profile')
        else:
            for field, errors in response.data.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    # For GET requests, render the edit form
    landlord_properties = Property.objects.filter(landlord__user=request.user)

    # Format the date for the form
    due_date = reminder.due_date.strftime('%Y-%m-%d')

    context = {
        'reminder': reminder,
        'landlord_properties': landlord_properties,
        'due_date': due_date
    }

    return render(request, 'edit_reminder.html', context)


@require_POST
@login_required
def delete_reminder(request, pk):
    """View to delete an existing reminder using the existing ReminderDetailAPIView"""
    # Use the existing APIView to handle the request
    detail_view = ReminderDetailAPIView()
    api_request = request._request

    # Call the delete method
    response = detail_view.delete(api_request, pk)

    # Handle the response
    if response.status_code == status.HTTP_204_NO_CONTENT:
        messages.success(request, "Reminder deleted successfully.")
    else:
        messages.error(request, "Failed to delete reminder.")

    return redirect('profile')
