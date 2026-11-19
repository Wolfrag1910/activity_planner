"""Small helpers for writing events in lists and cards."""

import datetime

from django import template
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from core.dates import day_and_month

register = template.Library()


@register.filter
def row_when(event):
    """
    The second line of an event row. The date block on the left already shows the
    weekday and day, so this shows the time; the date is added when the weekday
    alone would be ambiguous (past events, or more than a week away).
      '16:00–19:00'   '27–29 November'   '6 December · 18:00'
    """
    start = timezone.localtime(event.starts_at)
    if event.is_multi_day:
        end = timezone.localtime(event.ends_at)
        if start.month == end.month:
            return f"{start.day}–{day_and_month(end.date())}"
        return f"{day_and_month(start.date())} – {day_and_month(end.date())}"
    time = f"{start:%H:%M}"
    if event.ends_at is not None:
        time += f"–{timezone.localtime(event.ends_at):%H:%M}"
    today = timezone.localdate()
    if event.is_past or start.date() > today + datetime.timedelta(days=6):
        return f"{day_and_month(start.date())} · {time}"
    return time


def people_summary(going, maybe=0, spots_left=None):
    """'8 going · 1 maybe · 4 spots left' (each part only when it says something)."""
    parts = [ngettext("%(count)s going", "%(count)s going", going) % {"count": going}]
    if maybe:
        parts.append(ngettext("%(count)s maybe", "%(count)s maybe", maybe) % {"count": maybe})
    if spots_left == 0:
        parts.append(_("full"))
    elif spots_left is not None:
        parts.append(ngettext("%(count)s spot left", "%(count)s spots left", spots_left) % {"count": spots_left})
    return " · ".join(parts)


@register.simple_tag
def event_people(event):
    """People line for a card, from an event loaded with `with_details`."""
    spots_left = None if event.max_spots is None else max(event.max_spots - event.going_count, 0)
    return people_summary(event.going_count, spots_left=spots_left)
