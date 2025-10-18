from django.urls import path

from .views import (
    RentalAgreementListView,
    RentalAgreementCreateView,
    RentalAgreementUpdateView,
    RentalAgreementDeleteView,
    rental_agreement_details,
)

urlpatterns = [
    path("", RentalAgreementListView.as_view(), name="rentalagreement_list"),
    path("add/", RentalAgreementCreateView.as_view(), name="rentalagreement_add"),
    path("<int:pk>/edit/", RentalAgreementUpdateView.as_view(), name="rentalagreement_edit"),
    path("<int:pk>/delete/", RentalAgreementDeleteView.as_view(), name="rentalagreement_delete"),
    path("<int:pk>/details.json", rental_agreement_details, name="rentalagreement_details"),
]
