from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from debug_toolbar.toolbar import debug_toolbar_urls


urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("dashboard.urls")),
    path("", include("users.urls")),
    path("properties/", include("properties.urls")),
    path("leases/", include("leases.urls")),
    path("notifications/", include("notifications.urls")),
    path("messages/", include("messaging.urls")),

]

urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))] + debug_toolbar_urls()

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
