from urllib.parse import quote_plus

from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Category(models.TextChoices):
    OUTDOORS = "outdoors", _("Outdoors")
    TRIPS = "trips", _("Trips")
    VACATIONS = "vacations", _("Vacations")
    GAMING = "gaming", _("Gaming")


class EventQuerySet(models.QuerySet):
    def upcoming(self):
        """Events that haven't finished yet, cancelled ones included (they show as cancelled)."""
        now = timezone.now()
        return self.filter(Q(ends_at__gte=now) | Q(ends_at__isnull=True, starts_at__gte=now))


class Event(models.Model):
    """One plan: a hike, a trip, a holiday, a game night. See "What an event holds" in docs/PLAN.md."""

    class Status(models.TextChoices):
        # MVP events are published directly. "Proposed" and "voting" arrive with voting in v2.
        CONFIRMED = "confirmed", _("Confirmed")
        CANCELLED = "cancelled", _("Cancelled")

    category = models.CharField(_("category"), max_length=12, choices=Category.choices)
    title = models.CharField(_("title"), max_length=120)
    description = models.TextField(_("details"), blank=True)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="organized_events"
    )
    starts_at = models.DateTimeField(_("starts"))
    ends_at = models.DateTimeField(_("ends"), null=True, blank=True)
    place = models.CharField(_("where"), max_length=200, blank=True)
    max_spots = models.PositiveSmallIntegerField(_("spots"), null=True, blank=True)
    answer_by = models.DateTimeField(_("answer by"), null=True, blank=True)
    # Gaming extras (optional for other categories too).
    game = models.CharField(_("game"), max_length=100, blank=True)
    online_link = models.URLField(_("online link"), blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["starts_at"]
        verbose_name = _("event")
        verbose_name_plural = _("events")

    def __str__(self):
        return self.title

    # --- State -----------------------------------------------------------------

    @property
    def is_cancelled(self):
        return self.status == self.Status.CANCELLED

    @property
    def is_past(self):
        return (self.ends_at or self.starts_at) < timezone.now()

    @property
    def rsvp_open(self):
        """People can answer until the "answer by" time, or until the event starts."""
        if self.is_cancelled:
            return False
        closes = self.answer_by or self.starts_at
        return timezone.now() < closes

    def can_be_managed_by(self, member):
        """Only the organizer can edit or cancel an event; the admin can always step in."""
        return member.is_authenticated and (member == self.organizer or member.is_admin)

    # --- Spots -----------------------------------------------------------------

    @property
    def spots_taken(self):
        """Members going plus the guests they bring."""
        going = self.rsvps.filter(answer=RSVP.Answer.GOING)
        return going.count() + Guest.objects.filter(rsvp__in=going).count()

    @property
    def spots_left(self):
        if self.max_spots is None:
            return None
        return max(self.max_spots - self.spots_taken, 0)

    def has_room_for(self, extra_people):
        return self.max_spots is None or self.spots_taken + extra_people <= self.max_spots

    # --- Links -----------------------------------------------------------------

    @property
    def map_url(self):
        """Opens the place in Google Maps (or the phone's maps app)."""
        if not self.place:
            return ""
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(self.place)}"


class RSVP(models.Model):
    """A member's answer to an event: Going, Maybe or No (with a quick reason for Maybe and No)."""

    class Answer(models.TextChoices):
        GOING = "going", _("Going")
        MAYBE = "maybe", _("Maybe")
        NO = "no", _("No")

    class Reason(models.TextChoices):
        WORKING = "working", _("Working")
        AWAY = "away", _("Out of town")
        NOT_FEELING_IT = "not_feeling_it", _("Not feeling it")
        OTHER = "other", _("Other")

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rsvps")
    answer = models.CharField(max_length=5, choices=Answer.choices)
    reason = models.CharField(max_length=20, choices=Reason.choices, blank=True)
    note = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "member"], name="one_answer_per_member")]
        ordering = ["member__name"]

    def __str__(self):
        return f"{self.member} → {self.event}: {self.answer}"


class Guest(models.Model):
    """Someone a member brings (+1). Needs no account; the name is optional (surprise guests)."""

    rsvp = models.ForeignKey(RSVP, on_delete=models.CASCADE, related_name="guests")
    name = models.CharField(_("name"), max_length=60, blank=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.name or "+1"


def with_counts(events):
    """Add going/maybe counts to a list of events in one query (for lists and cards)."""
    return events.annotate(
        going_count=Count("rsvps", filter=Q(rsvps__answer=RSVP.Answer.GOING), distinct=True),
    )
