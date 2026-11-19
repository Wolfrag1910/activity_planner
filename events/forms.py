import datetime

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.forms import AccessibleErrorsMixin

from .models import RSVP, Category, Event

DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
TIME = forms.TimeInput(attrs={"type": "time"}, format="%H:%M")


def combine(day, time):
    """A date and a time from the form, as a Bucharest-time moment."""
    return timezone.make_aware(datetime.datetime.combine(day, time))


class EventForm(AccessibleErrorsMixin, forms.ModelForm):
    """
    Propose or edit an event. Dates and times are separate boxes on the page
    (as in the design); they're combined into moments here.
    """

    start_date = forms.DateField(label=_("Starts"), widget=DATE)
    start_time = forms.TimeField(label=_("At"), widget=TIME)
    end_date = forms.DateField(label=_("Ends"), widget=DATE, required=False)
    end_time = forms.TimeField(label=_("At"), widget=TIME, required=False)
    answer_by_date = forms.DateField(label=_("Day"), widget=DATE, required=False)
    answer_by_time = forms.TimeField(label=_("At"), widget=TIME, required=False)
    # Links typed without "https://" (e.g. "discord.gg/abc") get https added.
    online_link = forms.URLField(
        label=_("Online link"),
        required=False,
        assume_scheme="https",
        widget=forms.URLInput(attrs={"placeholder": "https://discord.gg/…"}),
    )

    class Meta:
        model = Event
        fields = ["category", "title", "place", "description", "max_spots", "game", "online_link"]
        labels = {
            "category": _("Category"),
            "title": _("Title"),
            "place": _("Where"),
            "description": _("Details"),
            "max_spots": _("Spots"),
            "game": _("Game"),
            "online_link": _("Online link"),
        }
        widgets = {
            "category": forms.RadioSelect,
            "description": forms.Textarea(attrs={"rows": 4}),
            "max_spots": forms.NumberInput(attrs={"min": 1, "max": 500}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = Category.choices  # no empty "------" option
        event = self.instance
        if event.pk:
            start = timezone.localtime(event.starts_at)
            self.initial.update(start_date=start.date(), start_time=start.time())
            if event.ends_at:
                end = timezone.localtime(event.ends_at)
                self.initial.update(end_date=end.date(), end_time=end.time())
            if event.answer_by:
                answer_by = timezone.localtime(event.answer_by)
                self.initial.update(answer_by_date=answer_by.date(), answer_by_time=answer_by.time())

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError(_("Please give the event a title."))
        return title

    def clean(self):
        data = super().clean()
        if self.errors.get("start_date") or self.errors.get("start_time"):
            return data
        starts = combine(data["start_date"], data["start_time"])
        data["starts_at"] = starts

        # End: optional. A time alone means the same day; a date alone means the end of that day.
        end_date, end_time = data.get("end_date"), data.get("end_time")
        ends = None
        if end_date or end_time:
            ends = combine(end_date or data["start_date"], end_time or datetime.time(23, 59))
            if ends <= starts:
                self.add_error("end_time" if end_time else "end_date", _("The end must be after the start."))
        data["ends_at"] = ends

        # Answer by: optional; a date alone means the end of that day.
        by_date, by_time = data.get("answer_by_date"), data.get("answer_by_time")
        answer_by = None
        if by_date or by_time:
            answer_by = combine(by_date or data["start_date"], by_time or datetime.time(23, 59))
            if answer_by > starts:
                self.add_error("answer_by_date", _("People need to answer before the event starts."))
        data["answer_by"] = answer_by
        return data

    def save(self, commit=True):
        event = super().save(commit=False)
        event.starts_at = self.cleaned_data["starts_at"]
        event.ends_at = self.cleaned_data["ends_at"]
        event.answer_by = self.cleaned_data["answer_by"]
        if commit:
            event.save()
        return event


class RSVPForm(AccessibleErrorsMixin, forms.Form):
    """Going / Maybe / No. Maybe and No need a quick reason; the note is optional."""

    answer = forms.ChoiceField(choices=RSVP.Answer.choices, widget=forms.RadioSelect)
    reason = forms.ChoiceField(choices=RSVP.Reason.choices, widget=forms.RadioSelect, required=False)
    note = forms.CharField(max_length=200, required=False, label=_("Note (optional)"))

    def __init__(self, *args, event=None, current=None, **kwargs):
        self.event = event
        self.current = current  # the member's existing RSVP, if any
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        answer = data.get("answer")
        if answer in (RSVP.Answer.MAYBE, RSVP.Answer.NO):
            if not data.get("reason"):
                self.add_error("reason", _("Pick a quick reason."))
        else:
            data["reason"], data["note"] = "", ""
        if answer == RSVP.Answer.GOING and self.event is not None:
            already_going = self.current is not None and self.current.answer == RSVP.Answer.GOING
            people = 1 + (self.current.guests.count() if self.current else 0)
            if not already_going and not self.event.has_room_for(people):
                self.add_error("answer", _("Sorry, the event is full."))
        return data


class GuestForm(AccessibleErrorsMixin, forms.Form):
    name = forms.CharField(max_length=60, required=False, label=_("Guest's name (optional)"))
