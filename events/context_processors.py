"""Values every page template needs from events."""

from .models import Category


def categories(request):
    """The four categories, for the desktop menu."""
    return {"event_categories": Category.choices}
