from django.contrib import admin
from .models import Reminder, TenantInvitation

admin.site.register(Reminder)
admin.site.register(TenantInvitation)