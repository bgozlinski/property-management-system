from django.urls import path
from . import views

urlpatterns = [
    path('send-invitation/', views.send_invitation, name='send_invitation'),
    path('accept-invitation/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
]