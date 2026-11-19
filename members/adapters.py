"""
Rules for Google sign-in (allauth).

- A Google account whose verified email belongs to a member signs that member in.
- A new Google account may only create a member when the visitor came through a
  valid invite link; the invite's name is used and the invite is used up.
- Anyone else is turned away with a friendly "ask for an invite" page.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import Invite, Member

PENDING_INVITE_SESSION_KEY = "pending_invite"


class MemberAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False  # members only join through invites

    def add_message(self, *args, **kwargs):
        pass  # no "Successfully signed in as ..." banners


class InviteOnlySocialAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Link a Google account to the existing member with the same (verified) email."""
        if sociallogin.is_existing:
            return
        email = (sociallogin.user.email or "").lower()
        verified = any(
            address.verified and address.email.lower() == email for address in sociallogin.email_addresses
        )
        if not (email and verified):
            return
        member = Member.objects.filter(email__iexact=email).first()
        if member is not None:
            sociallogin.connect(request, member)

    def is_open_for_signup(self, request, sociallogin):
        return pending_invite(request) is not None

    def populate_user(self, request, sociallogin, data):
        member = super().populate_user(request, sociallogin, data)
        invite = pending_invite(request)
        member.name = invite.name if invite else (data.get("name") or "")
        return member

    def save_user(self, request, sociallogin, form=None):
        member = super().save_user(request, sociallogin, form)
        invite = pending_invite(request)
        if invite is not None:
            invite.mark_used(member)
        request.session.pop(PENDING_INVITE_SESSION_KEY, None)
        return member


def pending_invite(request):
    """The usable invite this visitor opened earlier in their session, if any."""
    return Invite.usable(request.session.get(PENDING_INVITE_SESSION_KEY))
