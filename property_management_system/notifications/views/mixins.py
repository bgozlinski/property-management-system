from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from users.models import CustomUser, Landlord


class LandlordRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure only landlords can access the view.

    This mixin checks if the current user is authenticated and has the
    LANDLORD role before allowing access to the view.
    """

    def test_func(self):
        """
        Test if the current user is a landlord.

        Returns:
            bool: True if the user is authenticated, has the LANDLORD role,
                 and has an associated Landlord record, False otherwise.

        If the user has the LANDLORD role but doesn't have a Landlord record,
        a Landlord record will be automatically created for them.
        """
        if not (
            self.request.user.is_authenticated
            and self.request.user.role == CustomUser.RoleChoices.LANDLORD
        ):
            return False

        try:
            landlord = self.request.user.landlord
            if landlord is None:
                Landlord.objects.create(
                    user=self.request.user,
                    name=f"Landlord {self.request.user.email}",
                    contact_info="Please update your contact information",
                )
                messages.success(
                    self.request,
                    "A landlord profile has been automatically created for you.",
                )
                return True
            return True
        except (AttributeError, Exception):
            Landlord.objects.create(
                user=self.request.user,
                name=f"Landlord {self.request.user.email}",
                contact_info="Please update your contact information",
            )
            messages.success(
                self.request,
                "A landlord profile has been automatically created for you.",
            )
            return True
