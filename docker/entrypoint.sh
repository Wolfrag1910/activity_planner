#!/bin/sh
# Runs every time the website container starts: bring the database up to date,
# then start the web server (the command given in the Dockerfile).
set -e
python manage.py migrate --noinput
exec "$@"
