"""The rules for Google sign-in (members/adapters.py), tested without contacting Google."""

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from members.adapters import PENDING_INVITE_SESSION_KEY, InviteOnlySocialAdapter
from members.models import Invite, Member

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def google_configured(settings):
    """Pretend the Google login key is set up, as it will be on the server."""
    settings.SOCIALACCOUNT_PROVIDERS = {
        "google": {"APPS": [{"client_id": "test-id", "secret": "test-secret", "key": ""}]}
    }


def google_login(email, verified=True):
    """A pretend 'came back from Google' sign-in for this email."""
    user = Member(email=email)
    account = SocialAccount(provider="google", uid=f"google-{email}")
    return SocialLogin(
        user=user, account=account, email_addresses=[EmailAddress(email=email, verified=verified, primary=True)]
    )


def request_with_session(**session):
    request = RequestFactory().get("/")
    request.session = SessionStore()
    request.session.update(session)
    return request


def test_existing_member_is_recognised_by_verified_email():
    member = Member.objects.create_user(email="ana@example.com", name="Ana")
    sociallogin = google_login("Ana@Example.com")
    InviteOnlySocialAdapter().pre_social_login(request_with_session(), sociallogin)
    assert sociallogin.user == member
    assert SocialAccount.objects.filter(user=member, provider="google").exists()


def test_unverified_google_email_is_not_trusted():
    Member.objects.create_user(email="ana@example.com", name="Ana")
    sociallogin = google_login("ana@example.com", verified=False)
    InviteOnlySocialAdapter().pre_social_login(request_with_session(), sociallogin)
    assert not sociallogin.is_existing


def test_new_google_account_without_invite_is_turned_away():
    adapter = InviteOnlySocialAdapter()
    assert not adapter.is_open_for_signup(request_with_session(), google_login("new@example.com"))


def test_new_google_account_with_invite_may_join_and_uses_it_up():
    invite = Invite.objects.create(name="Bianca")
    request = request_with_session(**{PENDING_INVITE_SESSION_KEY: invite.token})
    adapter = InviteOnlySocialAdapter()
    sociallogin = google_login("bianca@gmail.com")
    assert adapter.is_open_for_signup(request, sociallogin)

    adapter.populate_user(request, sociallogin, {"email": "bianca@gmail.com", "name": "B. from Google"})
    member = adapter.save_user(request, sociallogin)

    assert member.name == "Bianca"  # the name from the invite, not from Google
    invite.refresh_from_db()
    assert invite.used_by == member
    assert PENDING_INVITE_SESSION_KEY not in request.session


def test_cancelled_invite_does_not_open_signup():
    invite = Invite.objects.create(name="Bianca")
    invite.cancel()
    request = request_with_session(**{PENDING_INVITE_SESSION_KEY: invite.token})
    assert not InviteOnlySocialAdapter().is_open_for_signup(request, google_login("b@gmail.com"))


def test_google_button_sends_visitor_to_google(client):
    response = client.post("/accounts/google/login/")
    assert response.status_code == 302
    assert response.url.startswith("https://accounts.google.com/")
    assert "client_id=test-id" in response.url
