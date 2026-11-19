"""The `seed_test_data` command: fake members and events for the private test (MVP step 6)."""

import datetime
import io
import re

import pytest
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse
from django.utils import timezone

from events.models import RSVP, Category, Event, Guest
from members.models import Invite, Member

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    return Member.objects.create_user(email="alex@example.com", name="Alex", language="en", is_admin=True)


def seed(*args):
    call_command("seed_test_data", *args, stdout=io.StringIO())


def fake(key):
    return Member.objects.get(email=f"{key}@cumetria.test")


def owners_events(owner):
    return Event.objects.upcoming().with_details(owner)


# --- Safety -----------------------------------------------------------------------------


def test_needs_the_owner_first():
    with pytest.raises(CommandError, match="create_owner"):
        seed()
    assert not Member.objects.exists()


def test_refuses_to_run_twice_without_reset(owner):
    seed()
    with pytest.raises(CommandError, match="--reset"):
        seed()
    assert Member.objects.filter(email__endswith="@cumetria.test").count() == 8


def test_reset_starts_over_without_duplicates(owner):
    seed()
    counts = (Member.objects.count(), Event.objects.count(), RSVP.objects.count(), Guest.objects.count())
    seed("--reset")
    assert (Member.objects.count(), Event.objects.count(), RSVP.objects.count(), Guest.objects.count()) == counts
    assert Invite.objects.count() == 2


def test_reset_leaves_real_members_and_their_events_alone(owner):
    friend = Member.objects.create_user(email="friend@example.com", name="Friend")
    real_invite = Invite.objects.create(name="Raluca", created_by=owner)
    seed()
    own_event = Event.objects.create(
        organizer=owner, category=Category.OUTDOORS, title="Mine", starts_at=timezone.now() + datetime.timedelta(days=3)
    )
    RSVP.objects.create(event=own_event, member=owner, answer=RSVP.Answer.GOING)
    RSVP.objects.create(event=own_event, member=fake("ana"), answer=RSVP.Answer.GOING)

    seed("--reset")

    assert Member.objects.filter(pk__in=[owner.pk, friend.pk]).count() == 2
    assert Invite.objects.filter(pk=real_invite.pk).exists()
    own_event.refresh_from_db()
    # The owner's answer stays; the old fake Ana's answer went with her.
    assert list(own_event.rsvps.values_list("member", flat=True)) == [owner.pk]
    assert owner.is_admin and Member.objects.get(pk=owner.pk).is_active


# --- What it creates -------------------------------------------------------------------


def test_creates_the_fake_group(owner):
    seed()
    fakes = Member.objects.filter(email__endswith="@cumetria.test")
    assert fakes.count() == 8
    assert not fakes.filter(is_admin=True).exists()
    assert not fake("mihai").is_active
    assert fake("bogdan").language == "en"
    assert Invite.objects.filter(used_at=None, cancelled_at=None).count() == 1
    assert Invite.objects.exclude(cancelled_at=None).count() == 1


def test_ioana_has_answered_nothing(owner):
    seed()
    assert not RSVP.objects.filter(member=fake("ioana")).exists()
    assert fake("ioana").birthday is None


def test_deactivated_member_keeps_past_answers(owner):
    seed()
    mihai_answers = Event.objects.filter(rsvps__member=fake("mihai"))
    assert mihai_answers.exists()
    assert all(event.is_past for event in mihai_answers)


def test_ana_has_the_next_birthday(owner):
    seed()
    today = timezone.localdate()
    assert fake("ana").next_birthday(today) == today + datetime.timedelta(days=5)


def test_every_category_has_upcoming_and_past_events(owner):
    seed()
    for category in Category.values:
        in_category = Event.objects.filter(category=category)
        assert in_category.upcoming().exists(), category
        assert in_category.past().exists(), category


def test_covers_the_scenarios_the_pages_need(owner):
    seed()
    today = timezone.localdate()
    upcoming = list(owners_events(owner))

    assert any(event.first_day == today for event in upcoming)  # today's plan
    assert any(event.first_day < today and event.happens_on(today) for event in upcoming)  # trip under way
    assert any(event.is_multi_day and event.first_day.isocalendar()[1] != event.last_day.isocalendar()[1]
               for event in upcoming)  # bar across two weeks
    assert any(event.is_multi_day and event.first_day.month != event.last_day.month
               for event in upcoming)  # bar across two months
    assert any(event.max_spots and event.spots_left == 0 for event in upcoming)  # full
    assert any(event.answer_by and not event.rsvp_open and not event.is_cancelled
               for event in upcoming)  # answers closed early
    assert any(event.is_cancelled for event in upcoming)
    assert any(event.is_cancelled for event in Event.objects.past())
    assert sum(event.needs_answer for event in upcoming) >= 2  # waiting for the owner's answer

    assert Guest.objects.filter(name="").exists() and Guest.objects.exclude(name="").exists()
    used_reasons = set(RSVP.objects.exclude(reason="").values_list("reason", flat=True))
    assert used_reasons == set(RSVP.Reason.values)
    assert RSVP.objects.exclude(note="").exists()


def test_dates_are_in_a_sensible_order(owner):
    """'Answer by' always comes before the start, and every end comes after its start."""
    seed()
    for event in Event.objects.all():
        if event.ends_at:
            assert event.ends_at > event.starts_at, event
        if event.answer_by:
            assert event.answer_by < event.starts_at, event


# --- Every page opens with the fake data ------------------------------------------------


def test_every_page_opens_for_the_owner(client, owner):
    seed()
    client.force_login(owner)
    next_month = (timezone.localdate().replace(day=1) + datetime.timedelta(days=32)).strftime("%Y-%m")
    urls = [
        reverse("home"),
        reverse("calendar"),
        reverse("calendar") + f"?month={next_month}",
        reverse("calendar") + "?view=list",
        reverse("explore"),
        reverse("members"),
        reverse("me"),
        reverse("admin_page"),
    ]
    urls += [reverse("category", args=[category]) for category in Category.values]
    urls += [reverse("category", args=[category]) + "?show=past" for category in Category.values]
    urls += [reverse("event", args=[event.pk]) for event in Event.objects.all()]
    urls += [reverse("member", args=[member.pk]) for member in Member.objects.filter(is_active=True)]
    for url in urls:
        assert client.get(url).status_code == 200, url
    for event in Event.objects.all():
        response = client.get(reverse("event_preview", args=[event.pk]), HTTP_HX_REQUEST="true")
        assert response.status_code == 200, event


def test_home_shows_todays_plans_and_waiting_answers(client, owner):
    seed()
    client.force_login(owner)
    page = client.get(reverse("home")).content.decode()
    assert "Picnic în Herăstrău" in page
    assert "Weekend la Sibiu" in page
    assert "Minecraft night" in page


def test_owner_can_sign_in_as_a_fake_member_with_an_email_link(client, owner):
    seed()
    client.post(reverse("request_sign_in_link"), {"email": "ana@cumetria.test"})
    assert mail.outbox[-1].to == ["ana@cumetria.test"]
    link = re.search(r"https?://\S+", mail.outbox[-1].body).group(0)
    client.post(link)
    page = client.get(reverse("home"))
    assert page.wsgi_request.user == fake("ana")
    # Ana is not the admin, so the Admin page is closed to her.
    assert client.get(reverse("admin_page")).status_code in (302, 403, 404)


def test_remove_takes_away_only_the_fake_data(owner):
    friend = Member.objects.create_user(email="friend@example.com", name="Friend")
    seed()
    seed("--remove")
    assert list(Member.objects.order_by("pk")) == [owner, friend]
    assert not Event.objects.exists()
    assert not Invite.objects.exists()


def test_remove_works_even_without_an_owner():
    seed("--remove")  # nothing to remove, no error
