from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from users.models import CustomUser
from .models import TenantInvitation
from .forms import TenantInvitationForm


@login_required
def send_invitation(request):
    # Sprawdź czy użytkownik jest wynajmującym
    if request.user.role != CustomUser.RoleChoices.LANDLORD:
        messages.error(request, "Tylko wynajmujący mogą wysyłać zaproszenia.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = TenantInvitationForm(request.POST, landlord=request.user)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.landlord = request.user
            invitation.save()

            # Generuj link do zaproszenia
            invitation_url = request.build_absolute_uri(
                reverse('accept_invitation', kwargs={'token': invitation.token})
            )

            # Przygotuj treść emaila
            subject = f"Zaproszenie do wynajmu nieruchomości: {invitation.property_unit}"
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

            # Wyślij email (w trybie deweloperskim zostanie wyświetlony w konsoli)
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
    invitation = get_object_or_404(TenantInvitation, token=token)

    # Sprawdź czy zaproszenie nie wygasło i jest oczekujące
    if invitation.is_expired:
        invitation.status = TenantInvitation.StatusChoices.EXPIRED
        invitation.save()
        messages.error(request, "To zaproszenie wygasło.")
        return redirect('login')

    if not invitation.is_pending:
        messages.error(request, "To zaproszenie zostało już wykorzystane lub odrzucone.")
        return redirect('login')

    # Jeśli użytkownik jest zalogowany
    if request.user.is_authenticated:
        # Sprawdź czy to ten sam email
        if request.user.email == invitation.email:
            # Akceptuj zaproszenie
            invitation.status = TenantInvitation.StatusChoices.ACCEPTED
            invitation.save()

            # Tutaj można dodać logikę tworzenia umowy najmu

            messages.success(request,
                             f"Zaproszenie do wynajmu nieruchomości {invitation.property_unit} zostało zaakceptowane.")
            return redirect('dashboard')
        else:
            messages.error(request, "To zaproszenie jest przeznaczone dla innego adresu email.")
            return redirect('dashboard')

    # Jeśli użytkownik nie jest zalogowany
    # Zapisz token w sesji i przekieruj do rejestracji
    request.session['invitation_token'] = str(invitation.token)
    messages.info(request, "Aby zaakceptować zaproszenie, zarejestruj się lub zaloguj.")

    # Jeśli użytkownik z tym emailem już istnieje, przekieruj do logowania
    if CustomUser.objects.filter(email=invitation.email).exists():
        return redirect('login')

    # W przeciwnym razie przekieruj do rejestracji
    return redirect('register')