
from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .views import RegisterView, ProfileView, ProfileUpdateView
from .forms import CustomPasswordResetForm, CustomPasswordChangeForm, CustomSetPasswordForm

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='sign-in.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    # Password change (requires login)
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='password_change_form.html',
        form_class=CustomPasswordChangeForm,
        success_url=reverse_lazy('password_change_done')
    ), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='password_change_done.html'
    ), name='password_change_done'),
    # Password reset (Forgot password)
    path('password/reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset_form.html',
        form_class=CustomPasswordResetForm,
        email_template_name='password_reset_email.txt',
        html_email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),
    path('password/reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html',
        form_class=CustomSetPasswordForm,
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),
]

