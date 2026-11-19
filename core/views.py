from django.http import HttpResponse
from django.shortcuts import render
from django.utils import formats, timezone, translation
from django.utils.translation import gettext_lazy as _

# Pages that exist in the menu but are built in later MVP steps.
# Each shows a short "coming later" note so the layout can be tried today.
PLACEHOLDER_PAGES = {
    "calendar": _("Calendar"),
    "explore": _("Explore"),
    "me": _("Me"),
    "propose": _("Propose an event"),
}


def friendly_date(day):
    """
    The date as people write it: "Thursday, 19 November" / "Joi, 19 noiembrie".
    Romanian writes month and weekday names in lowercase, so only the first
    letter is capitalised there.
    """
    text = formats.date_format(day, "l, j F")
    if translation.get_language() == "ro":
        text = text.lower().capitalize()
    return text


def home(request):
    return render(request, "core/home.html", {"today_label": friendly_date(timezone.localdate())})


def placeholder(request, page):
    return render(request, "core/placeholder.html", {"page_title": PLACEHOLDER_PAGES[page]})


def health(request):
    """Tiny page the server and Docker can poll to check the site is up."""
    return HttpResponse("ok", content_type="text/plain")
