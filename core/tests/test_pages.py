import pytest
from django.urls import reverse

from members.models import Member

MENU_PAGES = ["home", "calendar", "explore", "me", "propose"]

pytestmark = pytest.mark.django_db


@pytest.fixture
def client(client):
    """Every page needs a signed-in member: sign one in (Romanian, the default)."""
    client.force_login(Member.objects.create_user(email="alex@example.com", name="Alex"))
    return client


@pytest.mark.parametrize("name", MENU_PAGES)
def test_every_menu_page_opens(client, name):
    response = client.get(reverse(name))
    assert response.status_code == 200


def test_health_check(client):  # works signed in too
    response = client.get(reverse("health"))
    assert response.status_code == 200
    assert response.content == b"ok"


def test_page_carries_theme_attributes(client):
    html = client.get(reverse("home")).content.decode()
    assert 'data-look="picnic"' in html
    assert 'data-mode="light"' in html


def test_romanian_is_the_default_language(client):
    html = client.get(reverse("home")).content.decode()
    assert '<html lang="ro"' in html
    assert "Bine ai venit în Cumetria" in html


def test_switching_to_english(client):
    response = client.post(reverse("switch_language"), {"language": "en", "next": "/"})
    assert response.status_code == 302
    html = client.get(reverse("home")).content.decode()
    assert '<html lang="en"' in html
    assert "Welcome to Cumetria" in html


def test_switching_back_to_romanian(client):
    client.post(reverse("switch_language"), {"language": "en", "next": "/"})
    client.post(reverse("switch_language"), {"language": "ro", "next": "/"})
    html = client.get(reverse("home")).content.decode()
    assert "Bine ai venit în Cumetria" in html


def test_current_page_is_marked_in_menu(client):
    html = client.get(reverse("calendar")).content.decode()
    assert f'href="{reverse("calendar")}" aria-current="page"' in html


def test_pages_ask_search_engines_not_to_index(client):
    html = client.get(reverse("home")).content.decode()
    assert '<meta name="robots" content="noindex, nofollow">' in html


def test_romanian_date_uses_lowercase_month(client, settings):
    import datetime

    from django.utils import translation

    from core.views import friendly_date

    day = datetime.date(2026, 11, 19)
    with translation.override("ro"):
        assert friendly_date(day) == "Joi, 19 noiembrie"
    with translation.override("en"):
        assert friendly_date(day) == "Thursday, 19 November"
