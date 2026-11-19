"""
Make a backup of everything the site stores: the database and the uploaded photos.

    docker compose exec -T web python manage.py backup_data

Writes one file per run, e.g. /data/backups/cumetria-2026-11-19-0415.tar.gz, holding
  db.sqlite3   a consistent copy of the database (safe to take while the site runs)
  media/       the uploaded photos
and deletes the oldest files so only the newest --keep remain.

To restore, unpack the file into the data folder: see docs/DEPLOY.md.
"""

import sqlite3
import tarfile
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

FILE_PREFIX = "cumetria-"
FILE_SUFFIX = ".tar.gz"


def default_backup_dir():
    return Path(settings.DATA_DIR) / "backups"


def copy_database(destination):
    """
    Copy the live database with SQLite's own backup feature. Unlike copying the
    file, this gives a consistent snapshot even while someone is answering an event.
    """
    connection.ensure_connection()
    target = sqlite3.connect(destination)
    try:
        with target:
            connection.connection.backup(target)  # Django's open link to the database
    finally:
        target.close()


def make_backup(backup_dir):
    """Create one backup file in `backup_dir` and return its path."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = timezone.localtime().strftime("%Y-%m-%d-%H%M%S")
    final_path = backup_dir / f"{FILE_PREFIX}{stamp}{FILE_SUFFIX}"
    # Written under a temporary name first, so a half-written file never looks like a backup.
    partial_path = final_path.with_name(final_path.name + ".partial")

    with tempfile.TemporaryDirectory() as work_dir:
        database_copy = Path(work_dir) / "db.sqlite3"
        copy_database(database_copy)
        with tarfile.open(partial_path, "w:gz") as archive:
            archive.add(database_copy, arcname="db.sqlite3")
            media = Path(settings.MEDIA_ROOT)
            if media.is_dir():
                archive.add(media, arcname="media")

    partial_path.rename(final_path)
    return final_path


def remove_old_backups(backup_dir, keep):
    """Delete all but the newest `keep` backups. Returns the deleted paths."""
    backups = sorted(backup_dir.glob(f"{FILE_PREFIX}*{FILE_SUFFIX}"))  # names sort by date
    old = backups[:-keep] if keep > 0 else backups
    for path in old:
        path.unlink()
    return old


class Command(BaseCommand):
    help = "Back up the database and uploaded photos into one file (run nightly on the server)."

    def add_arguments(self, parser):
        parser.add_argument("--to", type=Path, default=None, help="Folder for the backups (default: DATA_DIR/backups).")
        parser.add_argument("--keep", type=int, default=14, help="How many backups to keep (default: 14).")

    def handle(self, *args, to, keep, **options):
        backup_dir = to or default_backup_dir()
        path = make_backup(backup_dir)
        removed = remove_old_backups(backup_dir, max(keep, 1))
        size_mb = path.stat().st_size / 1_000_000
        self.stdout.write(self.style.SUCCESS(f"Backup written: {path} ({size_mb:.1f} MB)"))
        if removed:
            self.stdout.write(f"Removed {len(removed)} older backup(s).")
