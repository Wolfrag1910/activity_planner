"""Step 5 polish: friendly error pages, plans on profiles, empty states."""

import datetime

import pytest
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from events.models import RSVP, Event, Guest
from members.models import Member

pytestmark = pytest.mark.django_db


@pytest.fixture
def ana():
    return Member.objects.create_user(email="ana@example.com", name="Ana", language="en")


@pytest.fixture
def mihai():
    return Member.objects.create_user(email="mihai@example.com", name="Mihai", language="en")


def event(organizer, title="Walk", days=2, **fields):
    day = timezone.localdate() + datetime.timedelta(days=days)
    starts = timezone.make_aware(datetime.datetime.combine(day, datetime.time(16, 0)))
    return Event.objects.create(organizer=organizer, category="outdoors", title=title, starts_at=starts, **fields)


def test_missing_page_is_friendly(client, ana):
    client.force_login(ana)
    response = client.get("/events/999/")
    assert response.status_code == 404
    assert "Nothing here" in response.content.decode()


def test_not_allowed_page_is_friendly(client, ana, mihai):
    walk = event(mihai)
    client.force_login(ana)
    response = client.get(reverse("event_edit", args=[walk.pk]))
    assert response.status_code == 403
    assert "Not for you, sorry" in response.content.decode()


def test_server_error_page_works_on_its_own():
    html = render_to_string("500.html")
    assert "Ceva n-a mers" in html and "Something went wrong" in html


def test_me_page_lists_my_plans(client, ana, mihai):
    going = event(mihai, "Going one")
    maybe = event(mihai, "Maybe one", days=3)
    no = event(mihai, "No one", days=4)
    RSVP.objects.create(event=going, member=ana, answer="going")
    RSVP.objects.create(event=maybe, member=ana, answer="maybe", reason="working")
    RSVP.objects.create(event=no, member=ana, answer="no", reason="away")
    client.force_login(ana)
    html = client.get(reverse("me")).content.decode()
    assert "Going one" in html and "Maybe one" in html and "No one" not in html


def test_member_page_lists_where_they_are_going(client, ana, mihai):
    walk = event(ana, "Walk with Mihai")
    event(ana, "Without Mihai", days=3)
    RSVP.objects.create(event=walk, member=mihai, answer="going")
    client.force_login(ana)
    html = client.get(reverse("member", args=[mihai.pk])).content.decode()
    assert "Walk with Mihai" in html and "Without Mihai" not in html


def test_past_event_says_who_went_without_an_empty_guest_box(client, ana):
    picnic = event(ana, "Picnic", days=-10)
    RSVP.objects.create(event=picnic, member=ana, answer="going")
    client.force_login(ana)
    html = client.get(reverse("event", args=[picnic.pk])).content.decode()
    assert "Who went" in html
    assert "guests-box" not in html


def test_past_event_still_lists_the_guests_you_brought(client, ana):
    picnic = event(ana, "Picnic", days=-10)
    Guest.objects.create(rsvp=RSVP.objects.create(event=picnic, member=ana, answer="going"), name="Matei")
    client.force_login(ana)
    html = client.get(reverse("event", args=[picnic.pk])).content.decode()
    assert "guests-box" in html and "Matei" in html and "Add guest" not in html


def test_lonely_admin_is_pointed_to_invites(client):
    owner = Member.objects.create_user(email="alex@example.com", name="Alex", language="en", is_admin=True)
    client.force_login(owner)
    html = client.get(reverse("members")).content.decode()
    assert "Just you so far" in html and reverse("admin_page") in html
