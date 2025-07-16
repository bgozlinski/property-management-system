from django.core.management.base import BaseCommand, CommandError
from users.factories import CustomUserFactory, TenantFactory, LandlordFactory



class Command(BaseCommand):
    help = "..."

    def handle(self, *args, **options):
        usr = LandlordFactory.create()
        print(usr)
        print(usr.user.role)