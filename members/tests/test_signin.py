import re

import pytest
from django.core import mail
from django.core.cache import cache
from django.urls import reverse

from members.models import Invite, Member

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def english_and_fresh_cache(client):
    """Read pages in English, and forget earlier "recently sent" emails between tests."""
    cache.clear()
    client.cookies["django_language"] = "en"


@pytest.fixture
def member():
    return Member.objects.create_user(email="ana@example.com", name="Ana", language="en")


def link_from_last_email():
    return re.search(r"https?://\S+", mail.outbox[-1].body).group(0)


# --- Every page needs a member ------------------------------------------------


def test_pages_redirect_visitors_to_login(client):
    response = client.get(reverse("home"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


def test_health_check_needs_no_login(client):
    assert client.get(reverse("health")).status_code == 200


def test_login_page_opens(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert "Email me a sign-in link" in response.content.decode()


def test_google_button_only_when_configured(client, settings):
    settings.GOOGLE_LOGIN_ENABLED = False
    assert "Continue with Google" not in client.get(reverse("login")).content.decode()
    settings.GOOGLE_LOGIN_ENABLED = True
    assert "Continue with Google" in client.get(reverse("login")).content.decode()


def test_allauth_login_page_redirects_to_ours(client):
    response = client.get("/accounts/login/")
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


# --- Emailed sign-in links ------------------------------------------------------


def test_member_gets_a_working_sign_in_link(client, member):
    response = client.post(reverse("request_sign_in_link"), {"email": "ANA@example.com"})
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ana@example.com"]

    link = link_from_last_email()
    assert client.get(link).status_code == 200  # opening the link only shows a button
    assert "_auth_user_id" not in client.session
    response = client.post(link)
    assert response.status_code == 302
    assert client.session["_auth_user_id"] == str(member.pk)


def test_sign_in_link_works_only_once(client, member):
    client.post(reverse("request_sign_in_link"), {"email": "ana@example.com"})
    link = link_from_last_email()
    client.post(link)
    client.post(reverse("logout"))
    assert client.post(link).status_code == 400


def test_sign_in_link_expires(client, member, settings):
    client.post(reverse("request_sign_in_link"), {"email": "ana@example.com"})
    link = link_from_last_email()
    settings.PASSWORD_RESET_TIMEOUT = -1
    assert client.post(link).status_code == 400


def test_unknown_email_gets_same_answer_but_no_email(client):
    response = client.post(reverse("request_sign_in_link"), {"email": "stranger@example.com"})
    assert response.status_code == 200
    assert "Check your email" in response.content.decode()
    assert mail.outbox == []


def test_deactivated_member_gets_no_link(client, member):
    member.is_active = False
    member.save()
    client.post(reverse("request_sign_in_link"), {"email": "ana@example.com"})
    assert mail.outbox == []


def test_link_for_deactivated_member_stops_working(client, member):
    client.post(reverse("request_sign_in_link"), {"email": "ana@example.com"})
    link = link_from_last_email()
    member.is_active = False
    member.save()
    assert client.post(link).status_code == 400


def test_second_request_within_a_minute_sends_nothing(client, member):
    client.post(reverse("request_sign_in_link"), {"email": "ana@example.com"})
    client.post(reverse("request_sign_in_link"), {"email": "ana@example.com"})
    assert len(mail.outbox) == 1


def test_invalid_email_shows_an_error(client):
    response = client.post(reverse("request_sign_in_link"), {"email": "not-an-email"})
    assert response.status_code == 400
    assert 'aria-invalid="true"' in response.content.decode()


# --- Joining through an invite ----------------------------------------------------


def test_invite_page_greets_by_name(client):
    owner = Member.objects.create_user(email="alex@example.com", name="Alex", is_admin=True)
    invite = Invite.objects.create(name="Bianca", created_by=owner)
    html = client.get(reverse("invite", args=[invite.token])).content.decode()
    assert "Alex" in html and "Bianca" in html


def test_used_or_unknown_invite_is_refused(client):
    assert client.get(reverse("invite", args=["no-such-token"])).status_code == 404
    invite = Invite.objects.create(name="Bianca")
    invite.cancel()
    assert client.get(reverse("invite", args=[invite.token])).status_code == 404


def test_joining_by_email(client):
    invite = Invite.objects.create(name="Bianca")
    client.get(reverse("invite", args=[invite.token]))
    client.post(reverse("invite_email", args=[invite.token]), {"email": "Bianca@Example.com"})
    assert mail.outbox[0].to == ["bianca@example.com"]

    link = link_from_last_email()
    assert client.get(link).status_code == 200
    assert not Member.objects.filter(email="bianca@example.com").exists()
    client.post(link)

    bianca = Member.objects.get(email="bianca@example.com")
    assert bianca.name == "Bianca"
    assert client.session["_auth_user_id"] == str(bianca.pk)
    invite.refresh_from_db()
    assert invite.used_by == bianca and not invite.is_usable


def test_invite_link_works_only_once(client):
    invite = Invite.objects.create(name="Bianca")
    client.post(reverse("invite_email", args=[invite.token]), {"email": "bianca@example.com"})
    link = link_from_last_email()
    client.post(link)
    client.post(reverse("logout"))
    assert client.post(link).status_code == 400
    assert Member.objects.filter(email="bianca@example.com").count() == 1


def test_invite_cannot_reuse_a_members_email(client, member):
    invite = Invite.objects.create(name="Someone")
    response = client.post(reverse("invite_email", args=[invite.token]), {"email": "ana@example.com"})
    assert response.status_code == 400
    assert "already belongs to a member" in response.content.decode()
    assert mail.outbox == []


def test_tampered_invite_link_is_refused(client):
    invite = Invite.objects.create(name="Bianca")
    other = Invite.objects.create(name="Cristi")
    client.post(reverse("invite_email", args=[invite.token]), {"email": "bianca@example.com"})
    payload = link_from_last_email().rstrip("/").split("/")[-1]
    assert client.post(reverse("invite_confirm", args=[other.token, payload])).status_code == 400
    assert client.post(reverse("invite_confirm", args=[invite.token, payload + "x"])).status_code == 400


# --- Signing out and language ------------------------------------------------------


def test_sign_out(client, member):
    client.force_login(member)
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session


def test_member_sees_their_own_language(client, member):
    member.language = "ro"
    member.save()
    client.force_login(member)
    assert '<html lang="ro"' in client.get(reverse("home")).content.decode()


def test_language_switch_is_saved_on_the_member(client, member):
    client.force_login(member)
    client.post(reverse("switch_language"), {"language": "ro", "next": "/"})
    member.refresh_from_db()
    assert member.language == "ro"


def test_language_switch_ignores_outside_redirects(client):
    response = client.post(reverse("switch_language"), {"language": "en", "next": "https://evil.example/"})
    assert response.url == "/"
