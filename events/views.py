from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.dates import event_when, lowercase_first

from .forms import EventForm, GuestForm, RSVPForm
from .models import RSVP, Category, Event, Guest


def answer_url(event):
    return reverse("event", args=[event.pk]) + "#your-answer"


# --- Proposing, editing, cancelling -----------------------------------------------


def propose(request):
    initial = {}
    if request.GET.get("category") in Category.values:
        initial["category"] = request.GET["category"]
    form = EventForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            # The organizer is going to their own event (if it has room for them).
            if event.has_room_for(1):
                RSVP.objects.create(event=event, member=request.user, answer=RSVP.Answer.GOING)
        return redirect("event", pk=event.pk)
    return render(request, "events/event_form.html", {"form": form, "is_new": True})


def manageable_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not event.can_be_managed_by(request.user):
        raise PermissionDenied
    return event


def edit(request, pk):
    event = manageable_event(request, pk)
    form = EventForm(request.POST or None, instance=event)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("event", pk=event.pk)
    return render(request, "events/event_form.html", {"form": form, "event": event, "is_new": False})


def cancel(request, pk):
    event = manageable_event(request, pk)
    if request.method == "POST":
        event.status = Event.Status.CANCELLED
        event.save(update_fields=["status", "updated_at"])
        return redirect("event", pk=event.pk)
    return render(request, "events/event_cancel.html", {"event": event})


# --- The event page ---------------------------------------------------------------------


def detail(request, pk):
    event = get_object_or_404(Event.objects.select_related("organizer"), pk=pk)
    return render_detail(request, event)


def render_detail(request, event, rsvp_form=None, status=200):
    """The event page. `rsvp_form` is passed back with error messages after a failed answer."""
    rsvps = list(event.rsvps.select_related("member").prefetch_related("guests"))
    mine = next((rsvp for rsvp in rsvps if rsvp.member_id == request.user.pk), None)
    going = [rsvp for rsvp in rsvps if rsvp.answer == RSVP.Answer.GOING]
    if rsvp_form is None:
        initial = {"answer": mine.answer, "reason": mine.reason, "note": mine.note} if mine else None
        rsvp_form = RSVPForm(initial=initial, event=event, current=mine)
    return render(
        request,
        "events/event_detail.html",
        {
            "event": event,
            "when": event_when(event.starts_at, event.ends_at),
            "answer_by": lowercase_first(event_when(event.answer_by)) if event.answer_by else "",
            "mine": mine,
            "rsvp_form": rsvp_form,
            "guest_form": GuestForm(),
            "going": going,
            "going_people": len(going) + sum(len(rsvp.guests.all()) for rsvp in going),
            "maybe": [rsvp for rsvp in rsvps if rsvp.answer == RSVP.Answer.MAYBE],
            "no": [rsvp for rsvp in rsvps if rsvp.answer == RSVP.Answer.NO],
            "can_manage": event.can_be_managed_by(request.user),
        },
        status=status,
    )


# --- Answering ----------------------------------------------------------------------------


@require_POST
def answer(request, pk):
    """
    Saves Going / Maybe / No. Sent from the event page (reloads the page) or from
    the quick preview (only the preview is redrawn, with "from=preview").
    """
    from .pages import render_preview

    event = get_object_or_404(Event.objects.select_related("organizer"), pk=pk)
    in_preview = request.POST.get("from") == "preview"
    if not event.rsvp_open:
        return render_preview(request, event) if in_preview else redirect(answer_url(event))
    mine = RSVP.objects.filter(event=event, member=request.user).first()
    form = RSVPForm(request.POST, event=event, current=mine)
    if not form.is_valid():
        if in_preview:
            return render_preview(request, event, rsvp_form=form)
        return render_detail(request, event, rsvp_form=form, status=400)
    data = form.cleaned_data
    with transaction.atomic():
        rsvp, _created = RSVP.objects.update_or_create(
            event=event,
            member=request.user,
            defaults={"answer": data["answer"], "reason": data["reason"], "note": data["note"]},
        )
        if rsvp.answer != RSVP.Answer.GOING:
            rsvp.guests.all().delete()  # guests come with you; not going means they aren't either
    if in_preview:
        return render_preview(request, event, saved=True)
    return redirect(answer_url(event))


@require_POST
def add_guest(request, pk):
    event = get_object_or_404(Event, pk=pk)
    mine = RSVP.objects.filter(event=event, member=request.user, answer=RSVP.Answer.GOING).first()
    form = GuestForm(request.POST)
    if mine is not None and event.rsvp_open and event.has_room_for(1) and form.is_valid():
        Guest.objects.create(rsvp=mine, name=form.cleaned_data["name"].strip())
    return redirect(answer_url(event))


@require_POST
def remove_guest(request, pk, guest_pk):
    guest = get_object_or_404(Guest, pk=guest_pk, rsvp__event_id=pk, rsvp__member=request.user)
    guest.delete()
    return redirect(answer_url(guest.rsvp.event))
