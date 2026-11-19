from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
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
    return render(request, "core/placeholder.html", {"page": page, "page_title": PLACEHOLDER_PAGES[page]})


@login_not_required
@require_POST
def switch_language(request):
    """
    The RO/EN button. Remembers the choice in a cookie (for visitors) and, for a
    signed-in member, on their account so every device follows it.
    """
    language = request.POST.get("language")
    next_url = request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/"
    response = HttpResponseRedirect(next_url)
    if language in dict(settings.LANGUAGES):
        if request.user.is_authenticated:
            request.user.language = language
            request.user.save(update_fields=["language"])
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language,
            max_age=365 * 24 * 3600,
            samesite="Lax",
            secure=settings.LANGUAGE_COOKIE_SECURE,
        )
    return response


@login_not_required
def health(request):
    """Tiny page the server and Docker can poll to check the site is up."""
    return HttpResponse("ok", content_type="text/plain")
