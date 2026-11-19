from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
    # Language switch: the RO/EN button posts here (Django's built-in view).
    path("i18n/", include("django.conf.urls.i18n")),
    # Django's own admin, for the owner only. The friendly Admin page comes in step 2.
    path("django-admin/", admin.site.urls),
]
