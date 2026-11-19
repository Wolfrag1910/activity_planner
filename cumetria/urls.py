from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", include("core.urls")),
    path("", include("members.urls")),
    path("", include("events.urls")),
    # allauth runs Google sign-in under /accounts/. Its own login page isn't used:
    # send anyone who lands there to ours. (This line must come before the include.)
    path("accounts/login/", RedirectView.as_view(pattern_name="login", query_string=True)),
    path("accounts/", include("allauth.urls")),
    # Django's own admin, a back door for the owner. The friendly Admin page comes in step 2b.
    path("django-admin/", admin.site.urls),
]
