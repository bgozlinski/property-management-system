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
from django.utils.translation import gettext as _


@login_required
def send_invitation(request):

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