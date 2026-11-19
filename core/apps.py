from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Shared pieces of the site: layout, home page, health check."""

    name = "core"
    default_auto_field = "django.db.models.BigAutoField"
