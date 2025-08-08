from django.urls import path
from . import views

urlpatterns = [
    path('', views.PropertyListView.as_view(), name='property_list'),
    path('<int:pk>/', views.PropertyDetailView.as_view(), name='property_detail'),

    # Class-based view routes
    path('add/', views.PropertyCreateView.as_view(), name='add_property'),
    path('edit/<int:pk>/', views.PropertyUpdateView.as_view(), name='edit_property'),
    path('delete/<int:pk>/', views.PropertyDeleteView.as_view(), name='delete_property'),

]