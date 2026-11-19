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

### First time: create your account and invites

With the site running, open a second terminal in the same folder:

```
docker compose exec web python manage.py create_owner --email you@gmail.com --name Alex
docker compose exec web python manage.py create_invite --name Bianca
```

The first makes you the admin. The second prints an invite link (until the Admin page arrives).

To sign in, open <http://localhost:8080>, type your email and press *Email me a sign-in link*. Locally no real email is sent: the email, with the link, appears in the `docker compose up` terminal.

*Continue with Google* appears once you set it up: see [`docs/GOOGLE_SIGN_IN.md`](docs/GOOGLE_SIGN_IN.md).

**Login photo:** put the group photo at `static/img/login-photo.jpg` and rebuild; until then the login page shows an empty frame.

## For development (without Docker)

```
pip install -r requirements-dev.txt
DJANGO_DEBUG=true python manage.py migrate
DJANGO_DEBUG=true python manage.py runserver
pytest
```

Romanian texts are in `locale/ro/LC_MESSAGES/django.po`; compile them with `python manage.py compilemessages` (needs GNU gettext). Docker and the GitHub checks do this automatically.
