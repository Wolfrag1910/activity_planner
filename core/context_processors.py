"""Values every page template needs."""

DEFAULT_LOOK = "picnic"
DEFAULT_MODE = "light"

# Looks and modes that have colours in static/css/themes.css. Postcard and dark
# mode arrive in v2; until then a member's saved choice falls back to the default.
STYLED_LOOKS = {"picnic"}
STYLED_MODES = {"light"}


def theme(request):
    """
    Which look and mode to draw the page in. They end up as attributes on <html>
    (data-look, data-mode), and the CSS picks the matching colour set.
    """
    member = getattr(request, "user", None)
    look, mode = DEFAULT_LOOK, DEFAULT_MODE
    if member is not None and member.is_authenticated:
        look = member.look if member.look in STYLED_LOOKS else DEFAULT_LOOK
        mode = member.mode if member.mode in STYLED_MODES else DEFAULT_MODE
    return {"theme_look": look, "theme_mode": mode}
