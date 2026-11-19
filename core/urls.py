from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("calendar/", views.placeholder, {"page": "calendar"}, name="calendar"),
    path("explore/", views.placeholder, {"page": "explore"}, name="explore"),
    path("language/", views.switch_language, name="switch_language"),
    path("media/<path:path>", views.media, name="media"),
    path("healthz", views.health, name="health"),
]
