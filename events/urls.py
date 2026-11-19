from django.urls import path

from . import pages, views

urlpatterns = [
    path("", pages.home, name="home"),
    path("explore/", pages.explore, name="explore"),
    path("explore/<slug:category>/", pages.category, name="category"),
    path("events/<int:pk>/preview/", pages.preview, name="event_preview"),
    path("propose/", views.propose, name="propose"),
    path("events/<int:pk>/", views.detail, name="event"),
    path("events/<int:pk>/edit/", views.edit, name="event_edit"),
    path("events/<int:pk>/cancel/", views.cancel, name="event_cancel"),
    path("events/<int:pk>/answer/", views.answer, name="event_answer"),
    path("events/<int:pk>/guests/", views.add_guest, name="event_add_guest"),
    path("events/<int:pk>/guests/<int:guest_pk>/remove/", views.remove_guest, name="event_remove_guest"),
]
