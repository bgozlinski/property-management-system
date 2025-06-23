from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.messages import get_messages

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('email')
            messages.success(request, f'Account created for {user}!')

            storage = get_messages(request)
            for message in storage:
                pass

            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'sign-up.html', {'form': form})