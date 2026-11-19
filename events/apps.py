from django.apps import AppConfig


class EventsConfig(AppConfig):
    """Events, answers (RSVPs) and guests."""

    name = "events"
    default_auto_field = "django.db.models.BigAutoField"
