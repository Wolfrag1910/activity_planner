import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from core.dates import event_when
from events.models import RSVP, Event, Guest
from members.models import Member

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    return Member.objects.create_user(email="alex@example.com", name="Alex", language="en", is_admin=True)


@pytest.fixture
def ana():
    return Member.objects.create_user(email="ana@example.com", name="Ana", language="en")


@pytest.fixture
def mihai():
    return Member.objects.create_user(email="mihai@example.com", name="Mihai", language="en")


def in_days(days, hour=16):
    day = timezone.localdate() + datetime.timedelta(days=days)
    return timezone.make_aware(datetime.datetime.combine(day, datetime.time(hour, 0)))


def make_event(organizer, **fields):
    defaults = {"category": "outdoors", "title": "Walk and mulled wine", "starts_at": in_days(2)}
    defaults.update(fields)
    return Event.objects.create(organizer=organizer, **defaults)


def form_data(**overrides):
    day = (timezone.localdate() + datetime.timedelta(days=2)).isoformat()
    data = {
        "category": "outdoors",
        "title": "Walk and mulled wine",
        "start_date": day,
        "start_time": "16:00",
        "end_date": "",
        "end_time": "19:00",
        "place": "Parcul Herăstrău",
        "description": "Bring gloves.",
        "max_spots": "12",
        "answer_by_date": "",
        "answer_by_time": "",
        "game": "",
        "online_link": "",
    }
    data.update(overrides)
    return data


# --- Readable times ------------------------------------------------------------------


def test_event_times_in_words():
    from django.utils import translation

    start = timezone.make_aware(datetime.datetime(2026, 11, 21, 16, 0))
    with translation.override("en"):
        assert event_when(start) == "Saturday, 21 November · 16:00"
        assert event_when(start, start + datetime.timedelta(hours=3)) == "Saturday, 21 November · 16:00–19:00"
        assert event_when(start, start + datetime.timedelta(days=2)) == "21 November, 16:00 – 23 November, 16:00"
    with translation.override("ro"):
        assert event_when(start) == "Sâmbătă, 21 noiembrie · 16:00"


# --- Proposing ------------------------------------------------------------------------


def test_propose_creates_event_and_organizer_is_going(client, ana):
    client.force_login(ana)
    response = client.post(reverse("propose"), form_data())
    event = Event.objects.get()
    assert response.status_code == 302 and response.url == reverse("event", args=[event.pk])
    assert event.organizer == ana
    assert timezone.localtime(event.starts_at).hour == 16
    assert timezone.localtime(event.ends_at).hour == 19
    assert event.max_spots == 12
    assert RSVP.objects.get(event=event, member=ana).answer == "going"


def test_propose_needs_title_category_and_start(client, ana):
    client.force_login(ana)
    response = client.post(reverse("propose"), form_data(title=" ", category="", start_date=""))
    assert response.status_code == 200
    html = response.content.decode()
    assert html.count('aria-invalid="true"') >= 3
    assert not Event.objects.exists()


def test_end_must_be_after_start(client, ana):
    client.force_login(ana)
    response = client.post(reverse("propose"), form_data(end_time="15:00"))
    assert "The end must be after the start" in response.content.decode()


def test_multi_day_trip(client, ana):
    client.force_login(ana)
    start = timezone.localdate() + datetime.timedelta(days=8)
    end = start + datetime.timedelta(days=2)
    client.post(
        reverse("propose"),
        form_data(category="trips", title="Cabin weekend", start_date=start.isoformat(), end_date=end.isoformat(), end_time="12:00"),
    )
    event = Event.objects.get()
    assert timezone.localtime(event.ends_at).date() == end


def test_answer_by_must_be_before_start(client, ana):
    client.force_login(ana)
    late = (timezone.localdate() + datetime.timedelta(days=5)).isoformat()
    response = client.post(reverse("propose"), form_data(answer_by_date=late))
    assert "answer before the event starts" in response.content.decode()


def test_gaming_link_gets_https(client, ana):
    client.force_login(ana)
    client.post(reverse("propose"), form_data(category="gaming", title="CS2 night", game="CS2", online_link="discord.gg/abc"))
    assert Event.objects.get().online_link == "https://discord.gg/abc"


def test_category_can_be_preselected(client, ana):
    client.force_login(ana)
    import re

    html = client.get(reverse("propose") + "?category=gaming").content.decode()
    checked = re.findall(r'<input[^>]*name="category"[^>]*>', html)
    assert [tag for tag in checked if "checked" in tag] == [t for t in checked if 'value="gaming"' in t]


# --- Editing and cancelling ------------------------------------------------------------


def test_only_organizer_or_admin_can_edit(client, owner, ana, mihai):
    event = make_event(ana)
    client.force_login(mihai)
    assert client.get(reverse("event_edit", args=[event.pk])).status_code == 403
    assert client.post(reverse("event_cancel", args=[event.pk])).status_code == 403
    client.force_login(ana)
    assert client.get(reverse("event_edit", args=[event.pk])).status_code == 200
    client.force_login(owner)
    assert client.get(reverse("event_edit", args=[event.pk])).status_code == 200


def test_edit_keeps_values_and_saves_changes(client, ana):
    event = make_event(ana, place="Herăstrău")
    client.force_login(ana)
    html = client.get(reverse("event_edit", args=[event.pk])).content.decode()
    assert "Herăstrău" in html and 'value="16:00"' in html
    client.post(reverse("event_edit", args=[event.pk]), form_data(title="Walk, wine and chestnuts"))
    event.refresh_from_db()
    assert event.title == "Walk, wine and chestnuts"


def test_cancel_closes_answers(client, ana, mihai):
    event = make_event(ana)
    client.force_login(ana)
    client.post(reverse("event_cancel", args=[event.pk]))
    event.refresh_from_db()
    assert event.is_cancelled and not event.rsvp_open
    client.force_login(mihai)
    client.post(reverse("event_answer", args=[event.pk]), {"answer": "going"})
    assert not RSVP.objects.filter(member=mihai).exists()
    assert "cancelled" in client.get(reverse("event", args=[event.pk])).content.decode().lower()


# --- Answering ---------------------------------------------------------------------------


def test_going(client, ana, mihai):
    event = make_event(ana)
    client.force_login(mihai)
    response = client.post(reverse("event_answer", args=[event.pk]), {"answer": "going"})
    assert response.status_code == 302 and response.url.endswith("#your-answer")
    assert RSVP.objects.get(event=event, member=mihai).answer == "going"


def test_maybe_needs_a_reason(client, ana, mihai):
    event = make_event(ana)
    client.force_login(mihai)
    response = client.post(reverse("event_answer", args=[event.pk]), {"answer": "maybe"})
    assert response.status_code == 400
    assert "Pick a quick reason" in response.content.decode()
    assert not RSVP.objects.filter(member=mihai).exists()


def test_no_with_reason_and_note_is_shown_to_everyone(client, ana, mihai):
    event = make_event(ana)
    client.force_login(mihai)
    client.post(reverse("event_answer", args=[event.pk]), {"answer": "no", "reason": "away", "note": "In Cluj that weekend"})
    client.force_login(ana)
    html = client.get(reverse("event", args=[event.pk])).content.decode()
    assert "Mihai" in html and "Out of town" in html and "In Cluj that weekend" in html


def test_changing_answer_updates_the_same_rsvp(client, ana, mihai):
    event = make_event(ana)
    client.force_login(mihai)
    client.post(reverse("event_answer", args=[event.pk]), {"answer": "maybe", "reason": "working"})
    client.post(reverse("event_answer", args=[event.pk]), {"answer": "going", "reason": "working", "note": "x"})
    rsvp = RSVP.objects.get(member=mihai)
    assert rsvp.answer == "going" and rsvp.reason == "" and rsvp.note == ""


def test_full_event_refuses_new_going(client, ana, mihai):
    event = make_event(ana, max_spots=1)
    RSVP.objects.create(event=event, member=ana, answer="going")
    client.force_login(mihai)
    response = client.post(reverse("event_answer", args=[event.pk]), {"answer": "going"})
    assert "the event is full" in response.content.decode()
    client.post(reverse("event_answer", args=[event.pk]), {"answer": "maybe", "reason": "other"})
    assert RSVP.objects.get(member=mihai).answer == "maybe"  # Maybe is still allowed


def test_answers_close_at_answer_by(client, ana, mihai):
    event = make_event(ana, answer_by=timezone.now() - datetime.timedelta(minutes=1))
    client.force_login(mihai)
    client.post(reverse("event_answer", args=[event.pk]), {"answer": "going"})
    assert not RSVP.objects.filter(member=mihai).exists()
    assert "Answers are closed" in client.get(reverse("event", args=[event.pk])).content.decode()


def test_answers_close_when_event_starts(client, ana, mihai):
    event = make_event(ana, starts_at=timezone.now() - datetime.timedelta(minutes=5))
    assert not event.rsvp_open


# --- Guests -------------------------------------------------------------------------------


def test_guests_count_toward_spots(client, ana, mihai):
    event = make_event(ana, max_spots=3)
    client.force_login(mihai)
    client.post(reverse("event_answer", args=[event.pk]), {"answer": "going"})
    client.post(reverse("event_add_guest", args=[event.pk]), {"name": "Matei"})
    client.post(reverse("event_add_guest", args=[event.pk]), {"name": ""})  # surprise guest
    assert event.spots_taken == 3 and event.spots_left == 0
    client.post(reverse("event_add_guest", args=[event.pk]), {"name": "One too many"})
    assert Guest.objects.count() == 2
    html = client.get(reverse("event", args=[event.pk])).content.decode()
    assert "Mihai + Matei + surprise guest" in html
    assert "3 of 3 spots taken" in html


def test_guests_need_a_going_answer(client, ana, mihai):
    event = make_event(ana)
    client.force_login(mihai)
    client.post(reverse("event_add_guest", args=[event.pk]), {"name": "Matei"})
    assert not Guest.objects.exists()


def test_saying_no_removes_your_guests(client, ana, mihai):
    event = make_event(ana)
    client.force_login(mihai)
    client.post(reverse("event_answer", args=[event.pk]), {"answer": "going"})
    client.post(reverse("event_add_guest", args=[event.pk]), {"name": "Matei"})
    client.post(reverse("event_answer", args=[event.pk]), {"answer": "no", "reason": "working"})
    assert not Guest.objects.exists()


def test_only_the_host_can_remove_their_guest(client, ana, mihai):
    event = make_event(ana)
    rsvp = RSVP.objects.create(event=event, member=mihai, answer="going")
    guest = Guest.objects.create(rsvp=rsvp, name="Matei")
    client.force_login(ana)
    assert client.post(reverse("event_remove_guest", args=[event.pk, guest.pk])).status_code == 404
    client.force_login(mihai)
    client.post(reverse("event_remove_guest", args=[event.pk, guest.pk]))
    assert not Guest.objects.exists()


# --- Pages ----------------------------------------------------------------------------------


def test_event_page_shows_details_and_map_link(client, ana, mihai):
    event = make_event(ana, place="Parcul Herăstrău", description="Bring gloves.")
    client.force_login(mihai)
    html = client.get(reverse("event", args=[event.pk])).content.decode()
    assert "Walk and mulled wine" in html and "Bring gloves." in html
    assert "https://www.google.com/maps/search/?api=1&amp;query=Parcul+Her%C4%83str%C4%83u" in html
    assert reverse("event_edit", args=[event.pk]) not in html  # not the organizer


def test_home_lists_upcoming_events_not_past_ones(client, ana):
    make_event(ana, title="Soon")
    make_event(ana, title="Long ago", starts_at=timezone.now() - datetime.timedelta(days=3))
    client.force_login(ana)
    html = client.get(reverse("home")).content.decode()
    assert "Soon" in html and "Long ago" not in html
