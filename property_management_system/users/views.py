from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.messages import get_messages
from .models import CustomUser


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Get the user object but don't save to DB yet
            if form.cleaned_data.get('is_landlord'):
                user.role = CustomUser.RoleChoices.LANDLORD
            user.save()  # Now save the user with the updated role

            email = form.cleaned_data.get('email')
            messages.success(request, f'Account created for {email}!')

            storage = get_messages(request)
            for message in storage:
                pass

            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'sign-up.html', {'form': form})
