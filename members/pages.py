"""The Me (profile) page and the Members pages."""

from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.dates import day_and_month

from .forms import ProfileForm
from .models import Member


def birthday_line(member, today):
    """Birthday text pieces for a member: ('3 March', 35) or (None, None)."""
    if not member.birthday:
        return None, None
    return day_and_month(member.birthday), member.age_at_next_birthday(today)


def plans_of(member, viewer, answers):
    """Upcoming events `member` answered with one of `answers`, as rows for `viewer`."""
    from events.models import Event

    return list(Event.objects.upcoming().active().answered_by(member, answers).with_details(viewer))


def profile(request):
    today = timezone.localdate()
    day, turns = birthday_line(request.user, today)
    return render(
        request,
        "members/profile.html",
        {
            "birthday_day": day,
            "birthday_turns": turns,
            "plans": plans_of(request.user, request.user, ["going", "maybe"]),
        },
    )


def profile_edit(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("me")
    return render(request, "members/profile_edit.html", {"form": form})


def upcoming_birthday(members, today):
    """The member whose birthday comes next (today counts), with the date, days to go and age."""
    candidates = [(m.next_birthday(today), m) for m in members if m.birthday]
    if not candidates:
        return None
    date, member = min(candidates, key=lambda pair: (pair[0], pair[1].name))
    return {
        "member": member,
        "date": day_and_month(date),
        "days": (date - today).days,
        "age": member.age_at_next_birthday(today),
    }


def members_list(request):
    today = timezone.localdate()
    members = list(Member.objects.filter(is_active=True))
    rows = []
    for member in members:
        day, turns = birthday_line(member, today)
        rows.append({"member": member, "birthday_day": day, "birthday_turns": turns})
    return render(
        request,
        "members/members_list.html",
        {"rows": rows, "next_birthday": upcoming_birthday(members, today)},
    )


def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk, is_active=True)
    day, turns = birthday_line(member, timezone.localdate())
    return render(
        request,
        "members/member_detail.html",
        {
            "member": member,
            "birthday_day": day,
            "birthday_turns": turns,
            "plans": plans_of(member, request.user, ["going"]),
        },
    )
