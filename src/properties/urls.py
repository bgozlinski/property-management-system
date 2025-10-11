from django.urls import path
from . import views

urlpatterns = [
    # Property routes (existing)
    path('', views.PropertyListView.as_view(), name='property_list'),
    path('add/', views.PropertyCreateView.as_view(), name='add_property'),
    path('<int:pk>/', views.PropertyDetailView.as_view(), name='property_detail'),
    path('edit/<int:pk>/', views.PropertyUpdateView.as_view(), name='edit_property'),
    path('delete/<int:pk>/', views.PropertyDeleteView.as_view(), name='delete_property'),

    # Building routes
    path('buildings/', views.BuildingListView.as_view(), name='building_list'),
    path('buildings/add/', views.BuildingCreateView.as_view(), name='add_building'),
    path('buildings/<int:pk>/', views.BuildingDetailView.as_view(), name='building_detail'),
    path('buildings/<int:pk>/edit/', views.BuildingUpdateView.as_view(), name='edit_building'),
    path('buildings/<int:pk>/delete/', views.BuildingDeleteView.as_view(), name='delete_building'),

    # Unit routes
    path('units/', views.UnitListView.as_view(), name='unit_list'),
    path('units/add/', views.UnitCreateView.as_view(), name='add_unit'),
    path('units/<int:pk>/', views.UnitDetailView.as_view(), name='unit_detail'),
    path('units/<int:pk>/edit/', views.UnitUpdateView.as_view(), name='edit_unit'),
    path('units/<int:pk>/delete/', views.UnitDeleteView.as_view(), name='delete_unit'),

    # Equipment routes
    path('equipment/add/', views.EquipmentCreateView.as_view(), name='add_equipment'),
    path('equipment/<int:pk>/edit/', views.EquipmentUpdateView.as_view(), name='edit_equipment'),
    path('equipment/<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='delete_equipment'),

    # Meter routes
    path('meters/add/', views.MeterCreateView.as_view(), name='add_meter'),
    path('meters/<int:pk>/edit/', views.MeterUpdateView.as_view(), name='edit_meter'),
    path('meters/<int:pk>/delete/', views.MeterDeleteView.as_view(), name='delete_meter'),
]