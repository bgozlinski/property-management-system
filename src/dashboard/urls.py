from django.urls import path, include
from .views import DashboardView, PaymentsMonthlyView, PaymentCreateView, PaymentUpdateView, PaymentDeleteView, TenantPaymentsView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('payments/', PaymentsMonthlyView.as_view(), name='payments_monthly'),
    path('payments/my/', TenantPaymentsView.as_view(), name='payments_tenant'),
    path('payments/add/', PaymentCreateView.as_view(), name='payment_add'),
    path('payments/<int:pk>/edit/', PaymentUpdateView.as_view(), name='payment_edit'),
    path('payments/<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),
    path('notifications/', include('notifications.urls')),

]