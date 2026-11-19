"""
Lays out a month for the calendar: weeks of days, each day with the coloured
dots (one-day events) and the bar (trips and other events over several days)
it should show. The templates only draw what this returns.
"""

import calendar as stdlib_calendar
import datetime
from dataclasses import dataclass, field

from django.db.models import Q
from django.utils import formats, timezone
from django.utils.translation import ngettext

from core.dates import _natural_case, friendly_date

from .models import Event

MAX_DOTS = 3


@dataclass
class Bar:
    """A stretch of a multi-day event on one day. Rounded where the event starts and ends."""

    category: str
    starts_here: bool
    ends_here: bool


@dataclass
class Day:
    date: datetime.date
    in_month: bool
    is_today: bool
    is_past: bool
    events: list = field(default_factory=list)
    dots: list = field(default_factory=list)  # categories of one-day events
    bar: Bar | None = None
    url: str = ""

    @property
    def label(self):
        """What a screen reader says for the day: 'Saturday, 28 November, 2 events'."""
        count = len(self.events)
        if not count:
            return friendly_date(self.date)
        return ngettext("%(day)s, %(count)s event", "%(day)s, %(count)s events", count) % {
            "day": friendly_date(self.date),
            "count": count,
        }


def month_title(first_day):
    """'November 2026' / 'Noiembrie 2026'."""
    return _natural_case(formats.date_format(first_day, "F Y"))


def weekday_letters():
    """First letter of each weekday, Monday first: M T W T F S S / L M M J V S D."""
    monday = datetime.date(2024, 1, 1)  # any Monday
    return [formats.date_format(monday + datetime.timedelta(days=i), "D")[0].upper() for i in range(7)]


def grid_days(first_day):
    """Every day shown for the month: from the Monday on or before the 1st to the Sunday after the last day."""
    last_day = first_day.replace(day=stdlib_calendar.monthrange(first_day.year, first_day.month)[1])
    start = first_day - datetime.timedelta(days=first_day.weekday())
    end = last_day + datetime.timedelta(days=6 - last_day.weekday())
    return [start + datetime.timedelta(days=i) for i in range((end - start).days + 1)]


def events_between(queryset, first, last):
    """Events taking place on any day from `first` to `last` (both included)."""
    start = timezone.make_aware(datetime.datetime.combine(first, datetime.time.min))
    end = timezone.make_aware(datetime.datetime.combine(last + datetime.timedelta(days=1), datetime.time.min))
    return queryset.filter(starts_at__lt=end).filter(Q(ends_at__gte=start) | Q(ends_at__isnull=True, starts_at__gte=start))


def build_month(first_day, events, today):
    """
    The month as a list of weeks (lists of 7 Days). `events` must already cover
    the whole grid (see events_between). Cancelled events are listed on their
    day but get no dot or bar.
    """
    days = [
        Day(date=day, in_month=day.month == first_day.month, is_today=day == today, is_past=day < today)
        for day in grid_days(first_day)
    ]
    for day in days:
        day.events = [event for event in events if event.happens_on(day.date)]
        for event in day.events:
            if event.is_cancelled:
                continue
            if event.is_multi_day:
                if day.bar is None:  # one bar per day; overlapping trips are rare
                    day.bar = Bar(event.category, event.first_day == day.date, event.last_day == day.date)
            elif event.category not in day.dots and len(day.dots) < MAX_DOTS:
                day.dots.append(event.category)
    return [days[i : i + 7] for i in range(0, len(days), 7)]


def day_of_trip(event, day):
    """(2, 3) for the second day of a three-day event."""
    return (day - event.first_day).days + 1, (event.last_day - event.first_day).days + 1


def month_events(first_day, member, category=None):
    """Events for a month grid, with the details lists need."""
    days = grid_days(first_day)
    queryset = Event.objects.with_details(member).order_by("starts_at")
    if category:
        queryset = queryset.filter(category=category)
    return list(events_between(queryset, days[0], days[-1]))
