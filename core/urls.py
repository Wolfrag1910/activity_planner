from django.urls import path

from . import views

urlpatterns = [
    path("language/", views.switch_language, name="switch_language"),
    path("media/<path:path>", views.media, name="media"),
    path("healthz", views.health, name="health"),
]
