from django.urls import path
from . import views

urlpatterns = [
    # UI Routes
    path('', views.property_list, name='property_list'),
    path('<int:pk>/', views.property_detail, name='property_detail'),

    # Class-based view routes
    path('add/', views.PropertyCreateView.as_view(), name='add_property'),
    path('edit/<int:pk>/', views.PropertyUpdateView.as_view(), name='edit_property'),
    path('delete/<int:pk>/', views.PropertyDeleteView.as_view(), name='delete_property'),

]