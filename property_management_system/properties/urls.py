from django.urls import path
from . import views

urlpatterns = [
    # UI Routes
    path('', views.property_list, name='property_list'),
    path('<int:pk>/', views.property_detail, name='property_detail'),

    # API Routes
    path('api/properties/', views.PropertyListCreateAPIView.as_view(), name='api_property_list'),
    path('api/properties/<int:pk>/', views.PropertyDetailAPIView.as_view(), name='api_property_detail'),
]