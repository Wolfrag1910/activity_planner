"""
The browsing pages: home, Explore, the category pages, and the quick preview
that opens when an event card is tapped.
"""

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from core.dates import event_when, friendly_date, lowercase_first
from members.models import Member
from members.pages import upcoming_birthday

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
    events = list(Event.objects.upcoming().with_details(request.user))
    active = [event for event in events if not event.is_cancelled]
    happening_today = [event for event in active if event.happens_on(today)]

    # The big card: today's first plan, or else the next one.
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
        },
    )


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
