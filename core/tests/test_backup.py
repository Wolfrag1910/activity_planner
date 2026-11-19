"""The nightly backup command (MVP step 6)."""

import io
import sqlite3
import tarfile

import pytest
from django.core.management import call_command

from core.management.commands.backup_data import remove_old_backups
from members.models import Member

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    (settings.MEDIA_ROOT / "members").mkdir(parents=True)
    (settings.MEDIA_ROOT / "members" / "ana.jpg").write_bytes(b"fake photo")
    return settings.MEDIA_ROOT


def backup(*args):
    out = io.StringIO()
    call_command("backup_data", *args, stdout=out)
    return out.getvalue()


def test_backup_holds_the_database_and_photos(tmp_path, media):
    Member.objects.create_user(email="ana@example.com", name="Ana")
    backup_dir = tmp_path / "backups"
    output = backup("--to", str(backup_dir))

    [file] = backup_dir.glob("cumetria-*.tar.gz")
    assert "Backup written" in output
    with tarfile.open(file) as archive:
        assert "media/members/ana.jpg" in archive.getnames()
        archive.extractall(tmp_path / "restored", filter="data")

    # The restore drill: the copied database opens and has Ana in it.
    restored = sqlite3.connect(tmp_path / "restored" / "db.sqlite3")
    names = [row[0] for row in restored.execute("SELECT name FROM members_member")]
    restored.close()
    assert names == ["Ana"]
    assert (tmp_path / "restored" / "media" / "members" / "ana.jpg").read_bytes() == b"fake photo"


def test_backup_works_without_any_photos(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path / "no-media-yet"
    backup("--to", str(tmp_path / "backups"))
    [file] = (tmp_path / "backups").glob("cumetria-*.tar.gz")
    with tarfile.open(file) as archive:
        assert archive.getnames() == ["db.sqlite3"]


def test_no_half_written_files_are_left(tmp_path, media):
    backup("--to", str(tmp_path / "backups"))
    assert not list((tmp_path / "backups").glob("*.partial"))


def test_only_the_newest_backups_are_kept(tmp_path):
    for day in range(1, 6):
        (tmp_path / f"cumetria-2026-11-0{day}-041500.tar.gz").write_bytes(b"")
    (tmp_path / "notes.txt").write_text("not a backup")

    removed = remove_old_backups(tmp_path, keep=3)

    assert [path.name for path in removed] == ["cumetria-2026-11-01-041500.tar.gz", "cumetria-2026-11-02-041500.tar.gz"]
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "cumetria-2026-11-03-041500.tar.gz",
        "cumetria-2026-11-04-041500.tar.gz",
        "cumetria-2026-11-05-041500.tar.gz",
        "notes.txt",
    ]


def test_keep_option_is_applied(tmp_path, media):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    for day in range(1, 4):
        (backup_dir / f"cumetria-2026-01-0{day}-041500.tar.gz").write_bytes(b"")
    backup("--to", str(backup_dir), "--keep", "2")
    names = sorted(path.name for path in backup_dir.iterdir())
    assert len(names) == 2
    assert names[0] == "cumetria-2026-01-03-041500.tar.gz"
