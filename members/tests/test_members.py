import pytest
from django.core.management import call_command

from members.models import Invite, Member

pytestmark = pytest.mark.django_db


def test_new_member_has_lowercase_email_and_no_password():
    member = Member.objects.create_user(email="Ana@Example.COM", name="Ana")
    assert member.email == "ana@example.com"
    assert not member.has_usable_password()
    assert member.language == "ro"
    assert member.look == "picnic"
    assert member.mode == "light"
    assert not member.is_admin


def test_only_admins_reach_django_admin():
    assert not Member.objects.create_user(email="a@example.com", name="A").is_staff
    assert Member.objects.create_user(email="b@example.com", name="B", is_admin=True).is_staff


def test_create_owner_command_creates_admin():
    call_command("create_owner", email="Alex@Example.com", name="Alex")
    owner = Member.objects.get(email="alex@example.com")
    assert owner.is_admin and owner.is_superuser and owner.name == "Alex"


def test_create_owner_command_promotes_existing_member():
    Member.objects.create_user(email="alex@example.com", name="Alex")
    call_command("create_owner", email="alex@example.com", name="Alex")
    assert Member.objects.get(email="alex@example.com").is_admin


def test_invite_lifecycle():
    invite = Invite.objects.create(name="Bianca")
    assert invite.is_usable
    assert Invite.usable(invite.token) == invite
    member = Member.objects.create_user(email="bianca@example.com", name="Bianca")
    invite.mark_used(member)
    assert not invite.is_usable
    assert Invite.usable(invite.token) is None


def test_cancelled_invite_is_not_usable():
    invite = Invite.objects.create(name="Cristi")
    invite.cancel()
    assert Invite.usable(invite.token) is None


def test_invite_tokens_are_unique_and_long():
    first, second = Invite.objects.create(name="A"), Invite.objects.create(name="B")
    assert first.token != second.token
    assert len(first.token) >= 30


def test_create_invite_command_prints_a_working_link(client, capsys):
    call_command("create_owner", email="alex@example.com", name="Alex")
    call_command("create_invite", name="Bianca", site="https://cumetria.test")
    link = capsys.readouterr().out.strip().splitlines()[-1]
    assert link.startswith("https://cumetria.test/invite/")
    invite = Invite.objects.get(name="Bianca")
    assert invite.created_by.email == "alex@example.com"
    assert client.get(link.replace("https://cumetria.test", "")).status_code == 200
