from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST


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


def media(request, path):
    """
    Uploaded files (member photos, later event albums), shown only to signed-in
    members. Serving them through Django instead of directly keeps them private.
    """
    root = Path(settings.MEDIA_ROOT).resolve()
    file_path = (root / path).resolve()
    if root not in file_path.parents or not file_path.is_file():
        raise Http404
    response = FileResponse(file_path.open("rb"))
    response["Cache-Control"] = "private, max-age=604800"
    return response


@login_not_required
def health(request):
    """Tiny page the server and Docker can poll to check the site is up."""
    return HttpResponse("ok", content_type="text/plain")
