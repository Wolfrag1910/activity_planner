# Cumetria (activity_planner)

A private, invite-only website for a group of about 9 friends to propose, vote on, RSVP to and remember shared plans: outdoor activities in Bucharest, trips in Romania and abroad, vacations and gaming sessions. Bilingual (Romanian and English), phone first, comfortable on desktop. Hosted on an Oracle Cloud free instance.

- **Plan:** [`docs/PLAN.md`](docs/PLAN.md): decisions, pages, releases (MVP, v2, v3) and data model
- **Designs:** [`docs/design/`](docs/design/): screens and design tokens for both looks
- **Build:** [`docs/BUILD.md`](docs/BUILD.md): tech stack (Django, HTMX, SQLite, Caddy, Docker Compose) and the MVP steps

Status: design done; building the MVP.

## Run it on your PC

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/).

1. Copy `.env.example` to `.env` and replace `DJANGO_SECRET_KEY` with a long random value:
   `python -c "import secrets; print(secrets.token_urlsafe(50))"`
2. Start everything: `docker compose up --build`
3. Open <http://localhost:8080>. Stop with `Ctrl+C`, or `docker compose down`.

The database and uploads live in a Docker volume, so they survive restarts.

## For development (without Docker)

```
pip install -r requirements-dev.txt
DJANGO_DEBUG=true python manage.py migrate
DJANGO_DEBUG=true python manage.py runserver
pytest
```

Romanian texts are in `locale/ro/LC_MESSAGES/django.po`; compile them with `python manage.py compilemessages` (needs GNU gettext). Docker and the GitHub checks do this automatically.
