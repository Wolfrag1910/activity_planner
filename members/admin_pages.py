"""The owner's Admin page: invites and deactivating members. Admins only."""

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import InviteForm
from .models import Invite, Member


def admin_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def invite_link(request, invite):
    return request.build_absolute_uri(reverse("invite", args=[invite.token]))


@admin_required
def admin_page(request, invite_form=None, new_invite=None):
    waiting = Invite.objects.filter(used_at=None, cancelled_at=None)
    return render(
        request,
        "members/admin.html",
        {
            "invite_form": invite_form or InviteForm(),
            "new_invite": new_invite,
            "new_invite_link": invite_link(request, new_invite) if new_invite else None,
            "waiting_invites": [(invite, invite_link(request, invite)) for invite in waiting],
            "members": Member.objects.order_by("-is_active", "name"),
        },
    )


@admin_required
@require_POST
def create_invite(request):
    form = InviteForm(request.POST)
    if not form.is_valid():
        return admin_page(request, invite_form=form)
    invite = form.save(commit=False)
    invite.created_by = request.user
    invite.save()
    # Show the page straight away (not a redirect) so the new link is right there to copy.
    return admin_page(request, new_invite=invite)


@admin_required
@require_POST
def cancel_invite(request, pk):
    invite = get_object_or_404(Invite, pk=pk, used_at=None)
    invite.cancel()
    return redirect("admin_page")


@admin_required
@require_POST
def set_member_active(request, pk, active):
    member = get_object_or_404(Member, pk=pk)
    if member.is_admin:
        raise PermissionDenied  # the admin can't switch themselves (or another admin) off
    member.is_active = active
    member.save(update_fields=["is_active"])
    return redirect("admin_page")
