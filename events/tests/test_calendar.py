"""The calendar: month layout, trip bars, filters and the list view (MVP step 4b)."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone, translation

from events import calendar
from events.models import Event
from members.models import Member

from .test_events import in_days, make_event

pytestmark = pytest.mark.django_db


@pytest.fixture
def ana():
    return Member.objects.create_user(email="ana@example.com", name="Ana", language="en")


def at(year, month, day, hour=16):
    return timezone.make_aware(datetime.datetime(year, month, day, hour))


# --- Month layout ------------------------------------------------------------------------------


def test_month_grid_runs_monday_to_sunday():
    november = calendar.grid_days(datetime.date(2026, 11, 1))  # 1 Nov 2026 is a Sunday
    assert november[0] == datetime.date(2026, 10, 26) and november[0].weekday() == 0
    assert november[-1] == datetime.date(2026, 12, 6) and november[-1].weekday() == 6
    assert len(calendar.grid_days(datetime.date(2027, 2, 1))) == 28  # February 2027 fits in four weeks


def test_weekday_letters_and_month_title():
    with translation.override("en"):
        assert "".join(calendar.weekday_letters()) == "MTWTFSS"
        assert calendar.month_title(datetime.date(2026, 11, 1)) == "November 2026"
    with translation.override("ro"):
        assert "".join(calendar.weekday_letters()) == "LMMJVSD"
        assert calendar.month_title(datetime.date(2026, 11, 1)) == "Noiembrie 2026"


def test_days_get_dots_and_trips_get_bars(ana):
    make_event(ana, category="outdoors", starts_at=at(2026, 11, 21))
    make_event(ana, category="gaming", starts_at=at(2026, 11, 21, 20))
    make_event(ana, category="trips", starts_at=at(2026, 11, 27), ends_at=at(2026, 11, 29, 12))
    make_event(ana, category="vacations", starts_at=at(2026, 11, 10), status="cancelled")
    first = datetime.date(2026, 11, 1)
    events = calendar.month_events(first, ana)
    days = {day.date.day: day for week in calendar.build_month(first, events, datetime.date(2026, 11, 19)) for day in week if day.in_month}

    assert days[21].dots == ["outdoors", "gaming"]
    assert (days[27].bar.starts_here, days[27].bar.ends_here) == (True, False)
    assert (days[28].bar.starts_here, days[28].bar.ends_here) == (False, False)
    assert (days[29].bar.starts_here, days[29].bar.ends_here) == (False, True)
    assert days[29].bar.category == "trips" and days[29].dots == []
    assert days[10].dots == [] and days[10].bar is None and len(days[10].events) == 1  # cancelled: listed only
    assert days[19].is_today and days[18].is_past and not days[20].is_past


def test_month_events_skip_events_outside_the_grid(ana):
    make_event(ana, title="October trip", starts_at=at(2026, 10, 1), ends_at=at(2026, 10, 3))
    make_event(ana, title="Overlaps grid", starts_at=at(2026, 10, 24), ends_at=at(2026, 10, 27))
    titles = [event.title for event in calendar.month_events(datetime.date(2026, 11, 1), ana)]
    assert titles == ["Overlaps grid"]


# --- Calendar page -----------------------------------------------------------------------------------


def test_calendar_opens_on_this_month_with_today_selected(client, ana):
    make_event(ana, title="Late walk", starts_at=timezone.make_aware(datetime.datetime.combine(timezone.localdate(), datetime.time(23, 0))))
    client.force_login(ana)
    response = client.get(reverse("calendar"))
    assert response.context["selected"] == timezone.localdate()
    assert "Late walk" in response.content.decode()
    assert 'aria-current="date"' in response.content.decode()


def test_selected_trip_day_says_which_day_it_is(client, ana):
    make_event(ana, title="Cabin weekend", category="trips", starts_at=at(2026, 11, 27), ends_at=at(2026, 11, 29, 12))
    client.force_login(ana)
    html = client.get(reverse("calendar") + "?month=2026-11&day=2026-11-28").content.decode()
    assert "Cabin weekend" in html and "Day 2 of 3" in html


def test_other_month_selects_its_first_busy_day(client, ana):
    make_event(ana, title="Market", starts_at=at(2030, 12, 6))
    client.force_login(ana)
    response = client.get(reverse("calendar") + "?month=2030-12")
    assert response.context["selected"] == datetime.date(2030, 12, 6)
    assert response.context["month_title"] == "December 2030"
    assert response.context["previous_url"].endswith("month=2030-11")
    assert response.context["next_url"].endswith("month=2031-01")


def test_category_filter(client, ana):
    make_event(ana, title="Walk", category="outdoors", starts_at=at(2030, 12, 6))
    make_event(ana, title="CS2 night", category="gaming", starts_at=at(2030, 12, 6, 21))
    client.force_login(ana)
    html = client.get(reverse("calendar") + "?month=2030-12&category=gaming").content.decode()
    assert "CS2 night" in html and "Walk" not in html
    assert 'class="filter-chip cat-gaming" href="/calendar/?month=2030-12&amp;category=gaming" aria-current="page"' in html


def test_bad_addresses_fall_back_to_this_month(client, ana):
    client.force_login(ana)
    response = client.get(reverse("calendar") + "?month=nonsense&day=99&category=knitting")
    assert response.status_code == 200
    assert response.context["selected"] == timezone.localdate() and response.context["category"] == ""


def test_list_view_groups_upcoming_events_by_month(client, ana):
    make_event(ana, title="Soon", starts_at=in_days(1))
    make_event(ana, title="Far", starts_at=in_days(70))
    make_event(ana, title="Over", starts_at=in_days(-5))
    client.force_login(ana)
    months = client.get(reverse("calendar") + "?view=list").context["months"]
    titles = [[event.title for event in events] for _title, events in months]
    assert [title for group in titles for title in group] == ["Soon", "Far"]
    assert len(months) >= 2  # 70 days later is always another month


def test_home_has_this_months_mini_calendar(client, ana):
    client.force_login(ana)
    response = client.get(reverse("home"))
    days = [day for week in response.context["mini_month"] for day in week if day.in_month]
    assert days[0].date == timezone.localdate().replace(day=1)
    assert days[0].url == reverse("calendar") + f"?day={days[0].date.isoformat()}"


def test_mini_calendar_link_opens_that_month(client, ana):
    client.force_login(ana)
    response = client.get(reverse("calendar") + "?day=2030-12-06")
    assert response.context["selected"] == datetime.date(2030, 12, 6)
    assert response.context["month_title"] == "December 2030"


def test_events_between_uses_whole_days(ana):
    event = make_event(ana, starts_at=at(2026, 11, 30, 23))
    found = calendar.events_between(Event.objects.all(), datetime.date(2026, 11, 30), datetime.date(2026, 11, 30))
    assert list(found) == [event]
