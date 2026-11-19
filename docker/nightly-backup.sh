#!/bin/sh
# Nightly backup, run on the server by cron (see docs/DEPLOY.md, "Nightly backup").
#
# 1. Asks the website to write a backup inside its data volume (keeps the last 14).
# 2. Copies the backups folder out of Docker to ~/cumetria-backups on the server.
# 3. Deletes copies there older than 14 days.
# 4. Copies them off the server (step to finish together; see DEPLOY.md).
#
# It only talks to the Cumetria containers; the game servers are never touched.
set -e

SITE_DIR="${SITE_DIR:-/opt/cumetria}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/cumetria-backups}"

cd "$SITE_DIR"
mkdir -p "$BACKUP_DIR"

docker compose exec -T web python manage.py backup_data --keep 14
docker compose cp web:/data/backups/. "$BACKUP_DIR/"
find "$BACKUP_DIR" -name 'cumetria-*.tar.gz' -mtime +14 -delete

# Off the server: uncomment once rclone is set up (DEPLOY.md, step 8).
# rclone copy "$BACKUP_DIR" cumetria-offsite:cumetria-backups --max-age 48h

echo "$(date '+%Y-%m-%d %H:%M') backup done"
