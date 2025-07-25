from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.conf import settings
from django.http import Http404
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Reminder, TenantInvitation
from .forms import TenantInvitationForm, ReminderForm
from users.models import CustomUser, Tenant
from properties.models import Property

from django.utils.translation import gettext as _


class LandlordRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only landlords can access the view"""

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == CustomUser.RoleChoices.LANDLORD
        )


class SendInvitationView(LoginRequiredMixin, LandlordRequiredMixin, FormView):
    template_name = "send_invitation.html"
    form_class = TenantInvitationForm
    success_url = reverse_lazy("profile")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["landlord"] = self.request.user
        return kwargs

    def form_valid(self, form):
        invitation = form.save(commit=False)
        invitation.landlord = self.request.user
        invitation.save()

        invitation_url = self.request.build_absolute_uri(
            reverse("accept_invitation", args=[invitation.token])
        )

        send_mail(
            _("Invitation to join Property Management System"),
            _(
                "You have been invited to join the Property Management System. "
                "Click the link to accept: {}"
            ).format(invitation_url),
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email],
            fail_silently=False,
        )

        messages.success(self.request, _("Invitation sent successfully!"))
        return super().form_valid(form)


class AcceptInvitationView(View):
    template_name = "accept_invitation.html"

    def get(self, request, token):
        invitation = get_object_or_404(
            TenantInvitation, token=token, status=TenantInvitation.StatusChoices.PENDING
        )

        if invitation.is_expired:
            messages.error(request, _("This invitation has expired."))
            return redirect("login")

        context = {"invitation": invitation}
        return render(request, self.template_name, context)

    def post(self, request, token):
        invitation = get_object_or_404(
            TenantInvitation, token=token, status=TenantInvitation.StatusChoices.PENDING
        )

        if invitation.is_expired:
            messages.error(request, _("This invitation has expired."))
            return redirect("login")

        try:
            user = CustomUser.objects.get(email=invitation.email)
            if user.role != CustomUser.RoleChoices.TENANT:
                user.role = CustomUser.RoleChoices.TENANT
                user.save()
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(
                email=invitation.email,
                password=request.POST.get("password"),
                role=CustomUser.RoleChoices.TENANT,
            )

        # Ensure a Tenant object exists for this user
        Tenant.objects.get_or_create(
            user=user,
            defaults={
                "name": invitation.email.split("@")[0],
                "contact_info": invitation.email,
            },
        )

        invitation.status = TenantInvitation.StatusChoices.ACCEPTED
        invitation.save()

        messages.success(
            request, _("Invitation accepted successfully! You can now log in.")
        )
        return redirect("login")


class ReminderCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    model = Reminder
    form_class = ReminderForm
    template_name = "add_reminder.html"
    success_url = reverse_lazy("profile")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["property"].queryset = Property.objects.filter(
            landlord__user=self.request.user
        )
        return form

    def form_valid(self, form):
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get("due_date") + " 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
        )

        property_obj = form.cleaned_data["property"]
        if property_obj.landlord.user != self.request.user:
            messages.error(
                self.request, "You can only create reminders for your own properties."
            )
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, "Reminder created successfully.")
        return response


class ReminderUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    model = Reminder
    form_class = ReminderForm
    template_name = "edit_reminder.html"
    success_url = reverse_lazy("profile")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["property"].queryset = Property.objects.filter(
            landlord__user=self.request.user
        )
        return form

    def get_object(self, queryset=None):
        reminder = super().get_object(queryset)
        if reminder.property.landlord.user != self.request.user:
            raise Http404("Reminder not found")
        return reminder

    def form_valid(self, form):
        form.instance.due_date = timezone.make_aware(
            timezone.datetime.strptime(
                self.request.POST.get("due_date") + " 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
        )

        property_obj = form.cleaned_data["property"]
        if property_obj.landlord.user != self.request.user:
            messages.error(
                self.request, "You can only assign reminders to your own properties."
            )
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, "Reminder updated successfully.")
        return response


class ReminderDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    model = Reminder
    success_url = reverse_lazy("profile")

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


#
# @login_required
# def add_reminder(request):
#     """View to add a new reminder using the existing ReminderListCreateAPIView"""
#     if request.method == 'POST':
#         if request.user.role != CustomUser.RoleChoices.LANDLORD:
#             messages.error(request, "Only landlords can create reminders.")
#             return redirect('profile')
#
#         try:
#             propert_id = request.POST.get('property')
#             property_obj = Property.objects.get(pk=propert_id)
#
#             if property_obj.landlord.user != request.user:
#                 messages.error(request, "You can only create reminders for your own properties.")
#                 return redirect('profile')
#
#             due_date = timezone.make_aware(
#                 timezone.datetime.strptime(
#                     request.POST.get('due_date') + ' 00:00:00',
#                     '%Y-%m-%d %H:%M:%S'
#                 )
#             )
#
#             reminder = Reminder(
#                 title=request.POST.get('title'),
#                 description=request.POST.get('description'),
#                 property=property_obj,
#                 due_date=due_date
#             )
#
#             reminder.save()
#             messages.success(request, "Reminder created successfully.")
#
#         except Property.DoesNotExist:
#             messages.error(request, "Property not found.")
#         except Exception as e:
#             messages.error(request, f"Error creating reminder: {str(e)}")
#
#     return redirect('profile')
#
#
# @login_required
# def edit_reminder(request, pk):
#     """View to edit an existing reminder directly using the model"""
#     try:
#         reminder = get_object_or_404(Reminder, pk=pk)
#
#         if reminder.property.landlord.user != request.user:
#             messages.error(request, "Reminder not found or you don't have permission to edit it.")
#             return redirect('profile')
#
#         if request.method == 'POST':
#             property_id = request.POST.get('property')
#             property_obj = Property.objects.get(pk=property_id)
#
#             if property_obj.landlord.user != request.user:
#                 messages.error(request, "You can only assign reminders to your own properties.")
#                 return redirect('profile')
#
#             due_date = timezone.make_aware(
#                 timezone.datetime.strptime(
#                     request.POST.get('due_date') + ' 00:00:00',
#                     '%Y-%m-%d %H:%M:%S'
#                 )
#             )
#
#             reminder.title = request.POST.get('title')
#             reminder.description = request.POST.get('description')
#             reminder.property = property_obj
#             reminder.due_date = due_date
#             reminder.save()
#
#             messages.success(request, "Reminder updated successfully.")
#             return redirect('profile')
#
#         landlord_properties = Property.objects.filter(landlord__user=request.user)
#
#         due_date = reminder.due_date.strftime('%Y-%m-%d')
#
#         context = {
#             'reminder': reminder,
#             'landlord_properties': landlord_properties,
#             'due_date': due_date
#         }
#
#         return render(request, 'edit_reminder.html', context)
#
#     except Reminder.DoesNotExist:
#         messages.error(request, "Reminder not found.")
#         return redirect('profile')
#     except Exception as e:
#         messages.error(request, f"Error updating reminder: {str(e)}")
#         return redirect('profile')
#
#
# @require_POST
# @login_required
# def delete_reminder(request, pk):
#     """View to delete an existing reminder directly using the model"""
#     try:
#         reminder = get_object_or_404(Reminder, pk=pk)
#
#         if reminder.property.landlord.user != request.user:
#             messages.error(request, "Reminder not found or you don't have permission to delete it.")
#             return redirect('profile')
#
#         reminder.delete()
#         messages.success(request, "Reminder deleted successfully.")
#
#     except Reminder.DoesNotExist:
#         messages.error(request, "Reminder not found.")
#     except Exception as e:
#         messages.error(request, f"Error deleting reminder: {str(e)}")
#
#     return redirect('profile')
