from django.contrib.auth.mixins import UserPassesTestMixin
from users.models import CustomUser


class LandlordRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only landlords can access the view"""

    def test_func(self):

        return (
            self.request.user.is_authenticated
            and self.request.user.role == CustomUser.RoleChoices.LANDLORD
        )
