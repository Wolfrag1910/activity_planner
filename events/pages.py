"""
The browsing pages: home, Explore, the category pages, and the quick preview
that opens when an event card is tapped.
"""

import datetime
from urllib.parse import urlencode

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from core.dates import event_when, friendly_date, lowercase_first
from members.models import Member
from members.pages import upcoming_birthday

from . import calendar
from .forms import RSVPForm
from .models import CATEGORY_BLURBS, RSVP, Category, Event
from .templatetags.event_tags import people_summary

HOME_UPCOMING_ROWS = 5
EVENING_STARTS_AT = 17  # an event starting from 17:00 is "tonight"


def is_htmx(request):
    """True when the request comes from htmx (a part of the page is being reloaded)."""
    return request.headers.get("HX-Request") == "true"


# --- Home ----------------------------------------------------------------------------


def home(request):
    today = timezone.localdate()
    first_of_month = today.replace(day=1)
    events = list(Event.objects.upcoming().with_details(request.user))
    active = [event for event in events if not event.is_cancelled]
    happening_today = [event for event in active if event.happens_on(today)]

    # The big card: today's most relevant plan (see todays_priority), or else the next one.
    happening_today.sort(key=lambda event: todays_priority(event, today))
    hero = (happening_today or active or [None])[0]
    others = [event for event in events if event != hero]
    waiting = [event for event in others if event.needs_answer]
    upcoming = [event for event in others if not event.needs_answer]

    return render(
        request,
        "events/home.html",
        {
            "today_label": friendly_date(today),
            "summary": home_summary(happening_today, waiting, today),
            "hero": hero,
            "hero_label": hero_label(hero, today) if hero else "",
            "hero_people": hero_people(hero) if hero else "",
            "category_counts": category_counts(active),
            "waiting": waiting,
            "upcoming": upcoming[:HOME_UPCOMING_ROWS],
            "more_upcoming": len(upcoming) > HOME_UPCOMING_ROWS,
            "member_count": Member.objects.filter(is_active=True).count(),
            # Small month calendar (desktop only).
            "mini_month": mini_month(first_of_month, request.user, today),
            "mini_month_title": calendar.month_title(first_of_month),
            "weekday_letters": calendar.weekday_letters(),
        },
    )


def todays_priority(event, today):
    """
    Which of today's events gets the big card. Lower comes first:
      0  you said Going or Maybe
      1  it starts today
      2  a trip that started earlier and is still under way
    Within a group, the earliest start comes first.
    """
    if event.my_answer in (RSVP.Answer.GOING, RSVP.Answer.MAYBE):
        group = 0
    elif event.first_day == today:
        group = 1
    else:
        group = 2
    return (group, event.starts_at)


def mini_month(first_of_month, member, today):
    """This month for the small calendar on the desktop home; each day links to it in the calendar."""
    weeks = calendar.build_month(first_of_month, calendar.month_events(first_of_month, member), today)
    for week in weeks:
        for day in week:
            day.url = calendar_url(day=day.date)
    return weeks


def home_summary(happening_today, waiting, today):
    """The few words after "Hi, Alex.": what today looks like."""
    count = len(happening_today)
    if count == 1:
        start = timezone.localtime(happening_today[0].starts_at)
        if start.date() == today and start.hour >= EVENING_STARTS_AT:
            return _("One plan tonight.")
    if count:
        return ngettext("One plan today.", "%(count)s plans today.", count) % {"count": count}
    if waiting:
        return ngettext(
            "One event is waiting for your answer.", "%(count)s events are waiting for your answer.", len(waiting)
        ) % {"count": len(waiting)}
    return ""


def hero_label(event, today):
    """'Today · 19:30', 'Today' (a trip already under way) or 'Next up · Saturday, 21 November · 16:00'."""
    start = timezone.localtime(event.starts_at)
    if start.date() == today:
        return _("Today · %(time)s") % {"time": f"{start:%H:%M}"}
    if event.happens_on(today):
        return _("Today")
    return _("Next up · %(when)s") % {"when": event_when(event.starts_at)}


def hero_people(event):
    """Going and spots for the big card, plus the first few faces."""
    going = [rsvp.member for rsvp in event.rsvps.filter(answer=RSVP.Answer.GOING).select_related("member")]
    spots_left = None if event.max_spots is None else max(event.max_spots - event.going_count, 0)
    return {"faces": going[:4], "text": people_summary(event.going_count, spots_left=spots_left)}


def category_counts(active_events):
    """[(category value, label, number of upcoming events)] for the shortcut buttons."""
    return [
        (value, label, sum(1 for event in active_events if event.category == value))
        for value, label in Category.choices
    ]


# --- Quick preview ---------------------------------------------------------------------


def preview(request, pk):
    """The sheet (phone) or side panel (desktop) that opens when an event card is tapped."""
    if not is_htmx(request):
        return redirect("event", pk=pk)
    event = get_object_or_404(Event.objects.select_related("organizer"), pk=pk)
    return render_preview(request, event)


def render_preview(request, event, rsvp_form=None, saved=False):
    rsvps = list(event.rsvps.select_related("member").prefetch_related("guests"))
    going = [rsvp for rsvp in rsvps if rsvp.answer == RSVP.Answer.GOING]
    going_people = len(going) + sum(len(rsvp.guests.all()) for rsvp in going)
    maybe = sum(1 for rsvp in rsvps if rsvp.answer == RSVP.Answer.MAYBE)
    mine = next((rsvp for rsvp in rsvps if rsvp.member_id == request.user.pk), None)
    if rsvp_form is None:
        initial = {"answer": mine.answer, "reason": mine.reason, "note": mine.note} if mine else None
        rsvp_form = RSVPForm(initial=initial, event=event, current=mine)
    spots_left = None if event.max_spots is None else max(event.max_spots - going_people, 0)
    response = render(
        request,
        "events/_preview.html",
        {
            "event": event,
            "when": event_when(event.starts_at, event.ends_at),
            "answer_by": lowercase_first(event_when(event.answer_by)) if event.answer_by else "",
            "faces": [rsvp.member for rsvp in going],
            "people": people_summary(going_people, maybe, spots_left),
            "mine": mine,
            "rsvp_form": rsvp_form,
            "in_preview": True,
            "saved": saved,
        },
    )
    if saved:
        # Tells the page underneath to refresh when the preview closes (static/js/preview.js).
        response["HX-Trigger"] = "answerSaved"
    return response


# --- Explore and category pages -----------------------------------------------------------


def explore(request):
    active = list(Event.objects.upcoming().active().select_related("organizer"))
    cards = []
    for value, label in Category.choices:
        in_category = [event for event in active if event.category == value]
        next_event = in_category[0] if in_category else None
        cards.append(
            {
                "category": value,
                "label": label,
                "count": len(in_category),
                "next": next_event,
                "next_is_today": next_event is not None and next_event.happens_on(timezone.localdate()),
            }
        )
    members = list(Member.objects.filter(is_active=True))
    return render(
        request,
        "events/explore.html",
        {
            "cards": cards,
            "member_count": len(members),
            "next_birthday": upcoming_birthday(members, timezone.localdate()),
        },
    )


LATELY_ROWS = 2


def category(request, category):
    if category not in Category.values:
        raise Http404
    show = "past" if request.GET.get("show") == "past" else "upcoming"
    in_category = Event.objects.filter(category=category).with_details(request.user)
    upcoming = list(in_category.upcoming())
    past = in_category.past()
    return render(
        request,
        "events/category.html",
        {
            "category": category,
            "label": Category(category).label,
            "blurb": CATEGORY_BLURBS[category],
            "show": show,
            "upcoming": upcoming,
            "upcoming_count": sum(1 for event in upcoming if not event.is_cancelled),
            "past": list(past) if show == "past" else list(past[:LATELY_ROWS]),
            "has_more_past": show == "upcoming" and past.count() > LATELY_ROWS,
        },
    )


# --- Calendar --------------------------------------------------------------------------------


def calendar_url(view="month", month=None, day=None, category=""):
    """A link to the calendar with the given choices (defaults are left out of the address)."""
    params = {}
    if view == "list":
        params["view"] = "list"
    if month:
        params["month"] = f"{month:%Y-%m}"
    if day:
        params["day"] = day.isoformat()
    if category:
        params["category"] = category
    return reverse("calendar") + (f"?{urlencode(params)}" if params else "")


def parse_month(text):
    """'2026-11' → 1 November 2026, or None."""
    try:
        month = datetime.datetime.strptime(text or "", "%Y-%m").date()
    except ValueError:
        return None
    return month if 2000 <= month.year <= 2100 else None


def parse_day(text):
    """'2026-11-28' → that date, or None."""
    try:
        day = datetime.date.fromisoformat(text or "")
    except ValueError:
        return None
    return day if 2000 <= day.year <= 2100 else None


def calendar_page(request):
    """
    The shared calendar. Month view: a month grid with coloured dots and trip bars,
    and the events of the selected day below it. List view: every upcoming event,
    grouped by month. Both can be filtered to one category.
    """
    today = timezone.localdate()
    view = "list" if request.GET.get("view") == "list" else "month"
    category = request.GET.get("category") if request.GET.get("category") in Category.values else ""
    selected = parse_day(request.GET.get("day"))
    month = parse_month(request.GET.get("month")) or (selected or today).replace(day=1)

    context = {
        "view": view,
        "category": category,
        "filters": [("", _("All"), calendar_url(view, month, category=""), category == "")]
        + [(value, label, calendar_url(view, month, category=value), category == value) for value, label in Category.choices],
        "month_url": calendar_url("month", month, category=category),
        "list_url": calendar_url("list", category=category),
    }
    if view == "list":
        context["months"] = upcoming_by_month(request.user, category)
    else:
        context.update(month_context(request.user, month, selected, today, category))
    return render(request, "events/calendar.html", context)


def month_context(member, month, selected, today, category):
    events = calendar.month_events(month, member, category)
    weeks = calendar.build_month(month, events, today)
    in_month = [day for week in weeks for day in week if day.in_month]
    if selected is None or selected.replace(day=1) != month:
        # Show today when looking at this month; otherwise the first day with something on.
        busy = [day.date for day in in_month if day.events]
        selected = today if today.replace(day=1) == month else (busy[0] if busy else None)
    for day in in_month:
        day.url = calendar_url("month", month, day.date, category)
    selected_events = [event for event in events if selected and event.happens_on(selected)]
    for event in selected_events:
        if event.is_multi_day:
            number, total = calendar.day_of_trip(event, selected)
            event.trip_day = _("Day %(number)s of %(total)s") % {"number": number, "total": total}
    previous_month = (month - datetime.timedelta(days=1)).replace(day=1)
    next_month = (month + datetime.timedelta(days=32)).replace(day=1)
    return {
        "weeks": weeks,
        "weekday_letters": calendar.weekday_letters(),
        "month_title": calendar.month_title(month),
        "previous_url": calendar_url("month", previous_month, category=category),
        "next_url": calendar_url("month", next_month, category=category),
        "today_url": calendar_url("month", category=category) if today.replace(day=1) != month else "",
        "selected": selected,
        "selected_label": friendly_date(selected) if selected else "",
        "selected_events": selected_events,
    }


def upcoming_by_month(member, category):
    """[(month title, [events])] for the list view."""
    events = Event.objects.upcoming().with_details(member)
    if category:
        events = events.filter(category=category)
    months = {}
    for event in events:
        first = timezone.localtime(event.starts_at).date().replace(day=1)
        months.setdefault(first, []).append(event)
    return [(calendar.month_title(first), month_events) for first, month_events in months.items()]
