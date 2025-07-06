from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.messages import get_messages
from django.utils import timezone

from .models import CustomUser, Tenant, Landlord
from notifications.models import Reminder
from properties.models import Property
from django.urls import reverse_lazy
from django.views.generic import FormView


class RegisterView(FormView):
    template_name = 'sign-up.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.save(commit=False)
        if form.cleaned_data.get('is_landlord'):
            user.role = CustomUser.RoleChoices.LANDLORD
        user.save()


        if user.role == CustomUser.RoleChoices.LANDLORD:
            Landlord.objects.create(
                user=user,
                name=f"Landlord {user.email}",  # Default name
                contact_info="Please update your contact information"  # Default contact info
            )
        else:
            Tenant.objects.create(
                user=user,
                name=f"Tenant {user.email}",  # Default name
                contact_info="Please update your contact information"  # Default contact info
            )

        email = form.cleaned_data.get('email')
        messages.success(self.request, f'Account created for {email}!')

        storage = get_messages(self.request)
        for message in storage:
            pass

        return super().form_valid(form)


@login_required
def profile(request):
    user = request.user
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
                ).order_by('due_date')

        except Landlord.DoesNotExist:
            pass
    elif user.role == CustomUser.RoleChoices.ADMINISTRATOR:
        role_name = "Administrator"

    context = {
        'user': user,
        'profile_data': profile_data,
        'role_name': role_name,
        'reminders': reminders,
        'landlord_properties': landlord_properties,
        'current_date': timezone.now()

    }

    return render(request, 'profile.html', context)
