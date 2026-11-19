"""Values every page template needs."""

# The looks and modes the site knows about. Only Sunday Picnic Light is styled
# in the MVP; Postcard and dark mode arrive in v2 (see docs/PLAN.md).
DEFAULT_LOOK = "picnic"
DEFAULT_MODE = "light"


def theme(request):
    """
    Which look and mode to draw the page in.

    They end up as attributes on <html> (data-look, data-mode), and the CSS picks
    the matching colour set. From step 2 on, a logged-in member's own choice
    (saved in their profile) will be used here instead of the defaults.
    """
    return {"theme_look": DEFAULT_LOOK, "theme_mode": DEFAULT_MODE}
