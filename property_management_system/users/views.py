from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.messages import get_messages
from django.utils import timezone

from .models import CustomUser, Tenant, Landlord
from notifications.models import Reminder
from properties.models import Property


def register(request): # CBV -> class based view.
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Get the user object but don't save to DB yet
            if form.cleaned_data.get('is_landlord'):
                user.role = CustomUser.RoleChoices.LANDLORD
            user.save()  # Now save the user with the updated role

            # Create the corresponding Tenant or Landlord instance
            if user.role == CustomUser.RoleChoices.LANDLORD:
                # Create a Landlord instance with default values
                Landlord.objects.create(
                    user=user,
                    name=f"Landlord {user.email}",  # Default name
                    contact_info="Please update your contact information"  # Default contact info
                )
            else:
                # Create a Tenant instance with default values
                Tenant.objects.create(
                    user=user,
                    name=f"Tenant {user.email}",  # Default name
                    contact_info="Please update your contact information"  # Default contact info
                )

            email = form.cleaned_data.get('email')
            messages.success(request, f'Account created for {email}!')

            storage = get_messages(request)
            for message in storage:
                pass

            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'sign-up.html', {'form': form})


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
