"""
Emailed sign-in links and invite confirmation links.

Sign-in link: for existing members. Works once (it stops matching as soon as the
member signs in, because their "last login" time changes) and expires after
SIGN_IN_LINK_MINUTES.

Invite confirmation link: for someone joining with an email address instead of
Google. It carries the invite and the email, signed so nobody can forge it, and
expires after INVITE_EMAIL_LINK_HOURS. It works once because the invite is used up.
"""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import signing
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext as _

from .models import Member

INVITE_LINK_SALT = "members.invite-email"
RESEND_WAIT_SECONDS = 60


class SignInLinkTokens(PasswordResetTokenGenerator):
    """Django's battle-tested reset-token maker, with its own salt so tokens can't be swapped."""

    key_salt = "members.SignInLinkTokens"


sign_in_link_tokens = SignInLinkTokens()


def recently_sent(email):
    """True if a link went to this address in the last minute (stops accidental or deliberate spamming)."""
    key = f"sign-in-email:{email.lower()}"
    if cache.get(key):
        return True
    cache.set(key, True, RESEND_WAIT_SECONDS)
    return False


# --- Sign-in links for members ------------------------------------------------


def sign_in_link(request, member):
    uid = urlsafe_base64_encode(force_bytes(member.pk))
    token = sign_in_link_tokens.make_token(member)
    return request.build_absolute_uri(reverse("sign_in_link", args=[uid, token]))


def send_sign_in_link(request, member):
    with translation.override(member.language):
        subject = _("Your sign-in link for Cumetria")
        body = render_to_string(
            "members/email/sign_in_link.txt",
            {"member": member, "link": sign_in_link(request, member), "minutes": settings.SIGN_IN_LINK_MINUTES},
        )
    send_mail(subject, body, None, [member.email])


def member_from_sign_in_link(uidb64, token):
    """The member this link belongs to, if the link is still valid; otherwise None."""
    try:
        pk = force_str(urlsafe_base64_decode(uidb64))
        member = Member.objects.get(pk=pk, is_active=True)
    except (ValueError, TypeError, OverflowError, Member.DoesNotExist):
        return None
    if sign_in_link_tokens.check_token(member, token):
        return member
    return None


# --- Invite confirmation links ------------------------------------------------


def invite_confirm_link(request, invite, email):
    payload = signing.dumps({"invite": invite.token, "email": email.lower()}, salt=INVITE_LINK_SALT)
    return request.build_absolute_uri(reverse("invite_confirm", args=[invite.token, payload]))


def send_invite_confirmation(request, invite, email):
    subject = _("Confirm your email to join Cumetria")
    body = render_to_string(
        "members/email/invite_confirm.txt",
        {"invite": invite, "link": invite_confirm_link(request, invite, email), "hours": settings.INVITE_EMAIL_LINK_HOURS},
    )
    send_mail(subject, body, None, [email])


def email_from_invite_link(invite, payload):
    """The email address in this confirmation link, if it's genuine, unexpired and for this invite."""
    try:
        data = signing.loads(payload, salt=INVITE_LINK_SALT, max_age=settings.INVITE_EMAIL_LINK_HOURS * 3600)
    except signing.BadSignature:
        return None
    if data.get("invite") != invite.token:
        return None
    return data.get("email")
