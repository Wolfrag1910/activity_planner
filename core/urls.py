from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("calendar/", views.placeholder, {"page": "calendar"}, name="calendar"),
    path("explore/", views.placeholder, {"page": "explore"}, name="explore"),
    path("me/", views.placeholder, {"page": "me"}, name="me"),
    path("propose/", views.placeholder, {"page": "propose"}, name="propose"),
    path("healthz", views.health, name="health"),
]
