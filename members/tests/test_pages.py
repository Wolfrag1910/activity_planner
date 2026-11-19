import datetime
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from core.dates import age_on, next_birthday
from members.models import Invite, Member
from members.pages import upcoming_birthday

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_in_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def owner():
    return Member.objects.create_user(email="alex@example.com", name="Alex", language="en", is_admin=True)


@pytest.fixture
def ana():
    return Member.objects.create_user(email="ana@example.com", name="Ana", language="en")


def photo_upload(width=2000, height=1500, with_location=True):
    """A JPEG like a phone would make, optionally with GPS data in it."""
    image = Image.new("RGB", (width, height), "orange")
    exif = Image.Exif()
    if with_location:
        exif[0x8825] = {1: "N", 2: (44.0, 26.0, 0.0)}  # GPS info block
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    return SimpleUploadedFile("holiday.jpg", buffer.getvalue(), content_type="image/jpeg")


# --- Birthdays -----------------------------------------------------------------


def test_next_birthday_and_age():
    born = datetime.date(1999, 11, 28)
    today = datetime.date(2026, 11, 19)
    assert next_birthday(born, today) == datetime.date(2026, 11, 28)
    assert age_on(born, datetime.date(2026, 11, 28)) == 27
    assert next_birthday(born, datetime.date(2026, 12, 1)) == datetime.date(2027, 11, 28)


def test_leap_day_birthday_in_ordinary_year():
    assert next_birthday(datetime.date(2000, 2, 29), datetime.date(2027, 1, 1)) == datetime.date(2027, 2, 28)


def test_upcoming_birthday_picks_the_nearest(owner, ana):
    today = datetime.date(2026, 11, 19)
    owner.birthday = datetime.date(1990, 3, 3)
    ana.birthday = datetime.date(1999, 11, 28)
    result = upcoming_birthday([owner, ana], today)
    assert result["member"] == ana and result["days"] == 9 and result["age"] == 27


# --- Me page -----------------------------------------------------------------------


def test_me_page_shows_name_and_admin_tools_for_admin(client, owner):
    client.force_login(owner)
    html = client.get(reverse("me")).content.decode()
    assert "Alex" in html
    assert reverse("admin_page") in html


def test_me_page_hides_admin_tools_from_members(client, ana):
    client.force_login(ana)
    assert reverse("admin_page") not in client.get(reverse("me")).content.decode()


def test_edit_profile(client, ana):
    client.force_login(ana)
    response = client.post(
        reverse("profile_edit"), {"name": "Ana Maria", "birthday": "1999-11-28", "language": "ro"}
    )
    assert response.status_code == 302
    ana.refresh_from_db()
    assert ana.name == "Ana Maria"
    assert ana.birthday == datetime.date(1999, 11, 28)
    assert ana.language == "ro"


def test_name_cannot_be_blank(client, ana):
    client.force_login(ana)
    response = client.post(reverse("profile_edit"), {"name": "   ", "language": "en"})
    assert response.status_code == 200
    assert 'aria-invalid="true"' in response.content.decode()
    ana.refresh_from_db()
    assert ana.name == "Ana"


def test_photo_is_shrunk_and_location_removed(client, ana):
    client.force_login(ana)
    client.post(reverse("profile_edit"), {"name": "Ana", "language": "en", "photo_upload": photo_upload()})
    ana.refresh_from_db()
    with Image.open(ana.photo.path) as saved:
        assert max(saved.size) == 600
        assert saved.format == "JPEG"
        assert 0x8825 not in saved.getexif()


def test_replacing_photo_deletes_the_old_file(client, ana):
    client.force_login(ana)
    client.post(reverse("profile_edit"), {"name": "Ana", "language": "en", "photo_upload": photo_upload()})
    ana.refresh_from_db()
    old_path = ana.photo.path
    client.post(reverse("profile_edit"), {"name": "Ana", "language": "en", "photo_upload": photo_upload()})
    ana.refresh_from_db()
    assert ana.photo.path != old_path
    assert not __import__("os").path.exists(old_path)


def test_remove_photo(client, ana):
    client.force_login(ana)
    client.post(reverse("profile_edit"), {"name": "Ana", "language": "en", "photo_upload": photo_upload()})
    client.post(reverse("profile_edit"), {"name": "Ana", "language": "en", "remove_photo": "on"})
    ana.refresh_from_db()
    assert not ana.photo


def test_non_image_upload_is_refused(client, ana):
    client.force_login(ana)
    fake = SimpleUploadedFile("notes.jpg", b"this is not a picture", content_type="image/jpeg")
    response = client.post(reverse("profile_edit"), {"name": "Ana", "language": "en", "photo_upload": fake})
    assert response.status_code == 200
    ana.refresh_from_db()
    assert not ana.photo


# --- Photos are private --------------------------------------------------------------


def test_photos_need_a_signed_in_member(client, ana):
    client.force_login(ana)
    client.post(reverse("profile_edit"), {"name": "Ana", "language": "en", "photo_upload": photo_upload()})
    ana.refresh_from_db()
    url = ana.photo.url
    assert client.get(url).status_code == 200
    client.post(reverse("logout"))
    response = client.get(url)
    assert response.status_code == 302 and response.url.startswith(reverse("login"))


def test_media_view_refuses_paths_outside_the_folder(client, ana):
    client.force_login(ana)
    assert client.get("/media/../cumetria/settings.py").status_code == 404
    assert client.get("/media/%2e%2e/%2e%2e/etc/passwd").status_code == 404


# --- Members ----------------------------------------------------------------------------


def test_members_list_shows_active_members_only(client, owner, ana):
    gone = Member.objects.create_user(email="old@example.com", name="Former Friend", is_active=False)
    client.force_login(ana)
    html = client.get(reverse("members")).content.decode()
    assert "Alex" in html and "Ana" in html
    assert gone.name not in html


def test_member_page(client, owner, ana):
    client.force_login(ana)
    assert "Alex" in client.get(reverse("member", args=[owner.pk])).content.decode()


def test_deactivated_member_page_is_gone(client, owner, ana):
    ana.is_active = False
    ana.save()
    client.force_login(owner)
    assert client.get(reverse("member", args=[ana.pk])).status_code == 404


# --- Admin page ------------------------------------------------------------------------


def test_admin_page_is_for_admins_only(client, ana):
    client.force_login(ana)
    assert client.get(reverse("admin_page")).status_code == 403
    assert client.post(reverse("create_invite"), {"name": "X"}).status_code == 403


def test_admin_creates_invite_and_sees_the_link(client, owner):
    client.force_login(owner)
    response = client.post(reverse("create_invite"), {"name": "Bianca"})
    invite = Invite.objects.get(name="Bianca")
    assert invite.created_by == owner
    assert reverse("invite", args=[invite.token]) in response.content.decode()


def test_invite_needs_a_name(client, owner):
    client.force_login(owner)
    response = client.post(reverse("create_invite"), {"name": "  "})
    assert 'aria-invalid="true"' in response.content.decode()
    assert not Invite.objects.exists()


def test_admin_cancels_invite(client, owner):
    invite = Invite.objects.create(name="Cristi", created_by=owner)
    client.force_login(owner)
    client.post(reverse("cancel_invite", args=[invite.pk]))
    invite.refresh_from_db()
    assert not invite.is_usable


def test_deactivating_a_member_signs_them_out(client, owner, ana):
    from django.test import Client

    ana_browser = Client()
    ana_browser.force_login(ana)
    assert ana_browser.get(reverse("home")).status_code == 200

    client.force_login(owner)
    client.post(reverse("deactivate_member", args=[ana.pk]))
    ana.refresh_from_db()
    assert not ana.is_active
    assert ana_browser.get(reverse("home")).status_code == 302  # sent to the login page

    client.post(reverse("reactivate_member", args=[ana.pk]))
    ana.refresh_from_db()
    assert ana.is_active


def test_admin_cannot_be_deactivated(client, owner):
    client.force_login(owner)
    assert client.post(reverse("deactivate_member", args=[owner.pk])).status_code == 403
    owner.refresh_from_db()
    assert owner.is_active
