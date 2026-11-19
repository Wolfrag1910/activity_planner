"""Home page, quick preview, Explore and category pages (MVP step 4a)."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone, translation

from events.models import RSVP, Event, Guest
from events.templatetags.event_tags import people_summary, row_when
from members.models import Member

from .test_events import in_days, make_event

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def ana():
    return Member.objects.create_user(email="ana@example.com", name="Ana", language="en")


@pytest.fixture
def mihai():
    return Member.objects.create_user(email="mihai@example.com", name="Mihai", language="en")


def local(day, hour, minute=0):
    return timezone.make_aware(datetime.datetime.combine(day, datetime.time(hour, minute)))


# --- Which events are upcoming or past -----------------------------------------------------


def test_event_without_end_stays_upcoming_until_the_end_of_its_day(ana):
    today = timezone.localdate()
    tonight = make_event(ana, title="Tonight", starts_at=local(today, 0, 1))  # already started
    yesterday = make_event(ana, title="Yesterday", starts_at=local(today - datetime.timedelta(days=1), 20))
    assert list(Event.objects.upcoming()) == [tonight]
    assert list(Event.objects.past()) == [yesterday]
    assert not tonight.is_past and yesterday.is_past


def test_trip_is_upcoming_until_it_ends(ana):
    trip = make_event(ana, starts_at=in_days(-2), ends_at=in_days(1))
    assert list(Event.objects.upcoming()) == [trip]
    assert trip.happens_on(timezone.localdate())


def test_upcoming_is_soonest_first_and_past_is_latest_first(ana):
    later = make_event(ana, title="Later", starts_at=in_days(9))
    sooner = make_event(ana, title="Sooner", starts_at=in_days(2))
    old = make_event(ana, title="Old", starts_at=in_days(-9))
    recent = make_event(ana, title="Recent", starts_at=in_days(-2))
    assert list(Event.objects.upcoming().with_details(ana)) == [sooner, later]
    assert list(Event.objects.past().with_details(ana)) == [recent, old]


def test_details_count_guests_and_know_my_answer(ana, mihai):
    event = make_event(ana)
    rsvp = RSVP.objects.create(event=event, member=mihai, answer="going")
    Guest.objects.create(rsvp=rsvp, name="Matei")
    RSVP.objects.create(event=event, member=ana, answer="maybe", reason="working")
    loaded = Event.objects.with_details(ana).get()
    assert loaded.going_count == 2
    assert loaded.answer_count == 2
    assert loaded.my_answer == "maybe"
    assert not loaded.needs_answer
    assert Event.objects.with_details(Member.objects.create_user(email="x@example.com", name="X")).get().needs_answer


# --- Small helpers -----------------------------------------------------------------------------


def test_row_times(ana):
    with translation.override("en"):
        soon = make_event(ana, starts_at=in_days(1), ends_at=in_days(1) + datetime.timedelta(hours=3))
        assert row_when(soon) == "16:00–19:00"
        far = make_event(ana, starts_at=local(timezone.localdate() + datetime.timedelta(days=20), 18))
        assert row_when(far).endswith(" · 18:00") and row_when(far)[0].isdigit()
        trip = make_event(ana, starts_at=local(datetime.date(2026, 11, 27), 16), ends_at=local(datetime.date(2026, 11, 29), 12))
        assert row_when(trip) == "27–29 November"
        long_trip = make_event(ana, starts_at=local(datetime.date(2026, 11, 30), 9), ends_at=local(datetime.date(2026, 12, 2), 18))
        assert row_when(long_trip) == "30 November – 2 December"


def test_people_summary():
    with translation.override("en"):
        assert people_summary(8, 1, 4) == "8 going · 1 maybe · 4 spots left"
        assert people_summary(1) == "1 going"
        assert people_summary(5, spots_left=0) == "5 going · full"
    with translation.override("ro"):
        assert people_summary(8, 1, 1) == "8 vin · 1 poate · 1 loc liber"


# --- Home ----------------------------------------------------------------------------------------


def test_home_big_card_is_todays_plan(client, ana, mihai):
    make_event(mihai, title="Next week walk", starts_at=in_days(6))
    make_event(mihai, title="Board games", category="gaming", starts_at=local(timezone.localdate(), 20, 30))
    client.force_login(ana)
    html = client.get(reverse("home")).content.decode()
    assert "One plan tonight." in html
    assert "Today · 20:30" in html
    assert html.index("Board games") < html.index("Next week walk")


def test_home_big_card_is_next_plan_when_nothing_today(client, ana, mihai):
    make_event(mihai, title="Cancelled one", starts_at=in_days(1), status="cancelled")
    make_event(mihai, title="Walk", starts_at=in_days(2))
    client.force_login(ana)
    response = client.get(reverse("home"))
    assert response.context["hero"].title == "Walk"  # cancelled events never get the big card
    assert "Next up · " in response.content.decode()


def test_home_separates_events_waiting_for_my_answer(client, ana, mihai):
    first = make_event(mihai, title="First", starts_at=in_days(1))
    answered = make_event(mihai, title="Answered", starts_at=in_days(2))
    unanswered = make_event(mihai, title="Unanswered", starts_at=in_days(3))
    RSVP.objects.create(event=answered, member=ana, answer="going")
    client.force_login(ana)
    context = client.get(reverse("home")).context
    assert context["hero"] == first
    assert context["waiting"] == [unanswered]
    assert context["upcoming"] == [answered]


def test_home_shows_category_counts(client, ana):
    make_event(ana, category="gaming", starts_at=in_days(1))
    make_event(ana, category="gaming", starts_at=in_days(2))
    make_event(ana, category="trips", starts_at=in_days(3), status="cancelled")
    client.force_login(ana)
    counts = {value: count for value, _label, count in client.get(reverse("home")).context["category_counts"]}
    assert counts == {"outdoors": 0, "trips": 0, "vacations": 0, "gaming": 2}


def test_home_with_no_events_invites_a_first_proposal(client, ana):
    client.force_login(ana)
    html = client.get(reverse("home")).content.decode()
    assert "Propose the first event" in html


# --- Quick preview ---------------------------------------------------------------------------------


def test_preview_opened_directly_goes_to_the_event_page(client, ana):
    event = make_event(ana)
    client.force_login(ana)
    response = client.get(reverse("event_preview", args=[event.pk]))
    assert response.status_code == 302 and response.url == reverse("event", args=[event.pk])


def test_preview_shows_essentials_and_answer_buttons(client, ana, mihai):
    event = make_event(mihai, place="Parcul Herăstrău", max_spots=5)
    RSVP.objects.create(event=event, member=mihai, answer="going")
    client.force_login(ana)
    html = client.get(reverse("event_preview", args=[event.pk]), **HTMX).content.decode()
    assert "Walk and mulled wine" in html and "Parcul Herăstrău" in html
    assert "1 going · 4 spots left" in html
    assert 'hx-post="%s"' % reverse("event_answer", args=[event.pk]) in html
    assert "<html" not in html  # only the panel, not a whole page


def test_answering_in_preview_redraws_the_preview(client, ana, mihai):
    event = make_event(mihai)
    client.force_login(ana)
    response = client.post(reverse("event_answer", args=[event.pk]), {"answer": "going", "from": "preview"}, **HTMX)
    assert response.status_code == 200
    assert response["HX-Trigger"] == "answerSaved"
    assert "Answer saved." in response.content.decode()
    assert RSVP.objects.get(event=event, member=ana).answer == "going"


def test_preview_shows_errors_without_saving(client, ana, mihai):
    event = make_event(mihai)
    client.force_login(ana)
    response = client.post(reverse("event_answer", args=[event.pk]), {"answer": "maybe", "from": "preview"}, **HTMX)
    assert response.status_code == 200  # htmx only redraws on success codes
    assert "HX-Trigger" not in response
    assert 'aria-invalid="true"' in response.content.decode() or "field-error" in response.content.decode()
    assert not RSVP.objects.exists()


# --- Explore and category pages ----------------------------------------------------------------------


def test_explore_shows_each_category_with_its_next_event(client, ana):
    make_event(ana, category="trips", title="Cabin weekend", starts_at=in_days(8))
    make_event(ana, category="trips", title="Sibiu", starts_at=in_days(20))
    client.force_login(ana)
    response = client.get(reverse("explore"))
    trips = next(card for card in response.context["cards"] if card["category"] == "trips")
    assert trips["count"] == 2 and trips["next"].title == "Cabin weekend"
    html = response.content.decode()
    assert "Cabin weekend" in html and reverse("category", args=["trips"]) in html
    assert reverse("members") in html


def test_category_page_lists_only_its_events(client, ana):
    make_event(ana, category="outdoors", title="Hike", starts_at=in_days(9))
    make_event(ana, category="outdoors", title="Picnic", starts_at=in_days(2))
    make_event(ana, category="gaming", title="CS2 night")
    client.force_login(ana)
    response = client.get(reverse("category", args=["outdoors"]))
    assert [event.title for event in response.context["upcoming"]] == ["Picnic", "Hike"]
    assert "CS2 night" not in response.content.decode()


def test_category_page_shows_lately_and_all_past_events(client, ana):
    for days in (-30, -20, -10):
        make_event(ana, category="outdoors", title=f"Past {days}", starts_at=in_days(days))
    client.force_login(ana)
    upcoming_tab = client.get(reverse("category", args=["outdoors"]))
    assert [event.title for event in upcoming_tab.context["past"]] == ["Past -10", "Past -20"]
    assert upcoming_tab.context["has_more_past"]
    past_tab = client.get(reverse("category", args=["outdoors"]) + "?show=past")
    assert [event.title for event in past_tab.context["past"]] == ["Past -10", "Past -20", "Past -30"]


def test_unknown_category_is_not_found(client, ana):
    client.force_login(ana)
    assert client.get(reverse("category", args=["knitting"])).status_code == 404


def test_desktop_menu_marks_the_current_category(client, ana):
    client.force_login(ana)
    html = client.get(reverse("category", args=["gaming"])).content.decode()
    assert f'href="{reverse("category", args=["gaming"])}" aria-current="page"' in html
