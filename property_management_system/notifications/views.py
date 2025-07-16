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
from .models import Reminder, TenantInvitation
from .forms import TenantInvitationForm, ReminderForm
from users.models import CustomUser
from properties.models import Property

from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

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


class LandlordRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only landlords can access the view"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == CustomUser.RoleChoices.LANDLORD


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
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get('due_date') + ' 00:00:00',
                '%Y-%m-%d %H:%M:%S'
            )
        )

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
        form.fields['property'].queryset = Property.objects.filter(landlord__user=self.request.user)
        return form

    def get_object(self, queryset=None):
        reminder = super().get_object(queryset)
        if reminder.property.landlord.user != self.request.user:
            raise Http404("Reminder not found")
        return reminder

    def form_valid(self, form):
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get('due_date') + ' 00:00:00',
                '%Y-%m-%d %H:%M:%S'
            )
        )

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
        return self.post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        reminder = super().get_object(queryset)
        if reminder.property.landlord.user != self.request.user:
            raise Http404("Reminder not found")
        return reminder

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Reminder deleted successfully.")
        return super().delete(request, *args, **kwargs)


@login_required
def add_reminder(request):
    """View to add a new reminder using the existing ReminderListCreateAPIView"""
    if request.method == 'POST':
        if request.user.role != CustomUser.RoleChoices.LANDLORD:
            messages.error(request, "Only landlords can create reminders.")
            return redirect('profile')

        try:
            propert_id = request.POST.get('property')
            property_obj = Property.objects.get(pk=propert_id)

            if property_obj.landlord.user != request.user:
                messages.error(request, "You can only create reminders for your own properties.")
                return redirect('profile')

            due_date = timezone.make_aware(
                timezone.datetime.strptime(
                    request.POST.get('due_date') + ' 00:00:00',
                    '%Y-%m-%d %H:%M:%S'
                )
            )

            reminder = Reminder(
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                property=property_obj,
                due_date=due_date
            )

            reminder.save()
            messages.success(request, "Reminder created successfully.")

        except Property.DoesNotExist:
            messages.error(request, "Property not found.")
        except Exception as e:
            messages.error(request, f"Error creating reminder: {str(e)}")

    return redirect('profile')


@login_required
def edit_reminder(request, pk):
    """View to edit an existing reminder directly using the model"""
    try:
        reminder = get_object_or_404(Reminder, pk=pk)

        if reminder.property.landlord.user != request.user:
            messages.error(request, "Reminder not found or you don't have permission to edit it.")
            return redirect('profile')

        if request.method == 'POST':
            property_id = request.POST.get('property')
            property_obj = Property.objects.get(pk=property_id)

            if property_obj.landlord.user != request.user:
                messages.error(request, "You can only assign reminders to your own properties.")
                return redirect('profile')

            due_date = timezone.make_aware(
                timezone.datetime.strptime(
                    request.POST.get('due_date') + ' 00:00:00',
                    '%Y-%m-%d %H:%M:%S'
                )
            )

            reminder.title = request.POST.get('title')
            reminder.description = request.POST.get('description')
            reminder.property = property_obj
            reminder.due_date = due_date
            reminder.save()

            messages.success(request, "Reminder updated successfully.")
            return redirect('profile')

        landlord_properties = Property.objects.filter(landlord__user=request.user)

        due_date = reminder.due_date.strftime('%Y-%m-%d')

        context = {
            'reminder': reminder,
            'landlord_properties': landlord_properties,
            'due_date': due_date
        }

        return render(request, 'edit_reminder.html', context)

    except Reminder.DoesNotExist:
        messages.error(request, "Reminder not found.")
        return redirect('profile')
    except Exception as e:
        messages.error(request, f"Error updating reminder: {str(e)}")
        return redirect('profile')


@require_POST
@login_required
def delete_reminder(request, pk):
    """View to delete an existing reminder directly using the model"""
    try:
        reminder = get_object_or_404(Reminder, pk=pk)

        if reminder.property.landlord.user != request.user:
            messages.error(request, "Reminder not found or you don't have permission to delete it.")
            return redirect('profile')

        reminder.delete()
        messages.success(request, "Reminder deleted successfully.")

    except Reminder.DoesNotExist:
        messages.error(request, "Reminder not found.")
    except Exception as e:
        messages.error(request, f"Error deleting reminder: {str(e)}")

    return redirect('profile')
