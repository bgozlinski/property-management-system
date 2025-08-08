
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import RegisterView, ProfileView

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='sign-in.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
]

