"""
Signing in, invites and signing out.

Every view here is marked @login_not_required because visitors use them before
they're signed in. Links from emails open a page with a button; the sign-in only
happens when the button is pressed. That stops email scanners, which open links
automatically, from using up a one-time link.
"""

from django import forms
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.contrib.staticfiles import finders
from django.shortcuts import redirect, render
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from . import signin
from .adapters import PENDING_INVITE_SESSION_KEY
from .models import Invite, Member

LOGIN_PHOTO = "img/login-photo.jpg"
BACKEND = "django.contrib.auth.backends.ModelBackend"


class EmailForm(forms.Form):
    email = forms.EmailField(label=_("Your email"), max_length=254)


def login_page_context(**extra):
    context = {
        "google_enabled": settings.GOOGLE_LOGIN_ENABLED,
        "login_photo": LOGIN_PHOTO if finders.find(LOGIN_PHOTO) else None,
        "email_form": EmailForm(),
    }
    context.update(extra)
    return context


# --- Members signing in ----------------------------------------------------------


@login_not_required
def login_page(request):
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "members/login.html", login_page_context())


@login_not_required
@require_POST
def request_sign_in_link(request):
    form = EmailForm(request.POST)
    if not form.is_valid():
        return render(request, "members/login.html", login_page_context(email_form=form), status=400)
    email = form.cleaned_data["email"]
    member = Member.objects.filter(email__iexact=email, is_active=True).first()
    # Same answer whether or not the address belongs to a member, so the page
    # can't be used to find out who is in the group.
    if member is not None and not signin.recently_sent(email):
        signin.send_sign_in_link(request, member)
    return render(request, "members/check_email.html", {"email": email})


@login_not_required
def sign_in_with_link(request, uidb64, token):
    member = signin.member_from_sign_in_link(uidb64, token)
    if member is None:
        return render(request, "members/link_invalid.html", status=400)
    if request.method == "POST":
        login(request, member, backend=BACKEND)
        return redirect("home")
    return render(request, "members/link_confirm.html", {"member": member})


# --- New members joining through an invite -----------------------------------------


@login_not_required
def invite_page(request, token):
    invite = Invite.usable(token)
    if invite is None:
        return render(request, "members/invite_invalid.html", status=404)
    # Remembered for Google sign-in, which leaves the site and comes back.
    request.session[PENDING_INVITE_SESSION_KEY] = invite.token
    return render(request, "members/login.html", login_page_context(invite=invite))


@login_not_required
@require_POST
def invite_email(request, token):
    invite = Invite.usable(token)
    if invite is None:
        return render(request, "members/invite_invalid.html", status=404)
    form = EmailForm(request.POST)
    if form.is_valid() and Member.objects.filter(email__iexact=form.cleaned_data["email"]).exists():
        form.add_error("email", _("This email already belongs to a member. Sign in from the start page instead."))
    if not form.is_valid():
        return render(
            request, "members/login.html", login_page_context(invite=invite, email_form=form), status=400
        )
    email = form.cleaned_data["email"].lower()
    if not signin.recently_sent(email):
        signin.send_invite_confirmation(request, invite, email)
    return render(request, "members/check_email.html", {"email": email, "invite": invite})


@login_not_required
def invite_confirm(request, token, payload):
    invite = Invite.usable(token)
    email = signin.email_from_invite_link(invite, payload) if invite else None
    if invite is None or email is None or Member.objects.filter(email__iexact=email).exists():
        return render(request, "members/link_invalid.html", status=400)
    if request.method == "POST":
        member = Member.objects.create_user(
            email=email, name=invite.name, language=translation.get_language() or "ro"
        )
        invite.mark_used(member)
        request.session.pop(PENDING_INVITE_SESSION_KEY, None)
        login(request, member, backend=BACKEND)
        return redirect("home")
    return render(request, "members/invite_confirm.html", {"invite": invite, "email": email})
