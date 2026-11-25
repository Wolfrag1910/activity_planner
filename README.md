# Cumetria (activity_planner)

A private, invite-only website for a group of about 9 friends to propose, vote on, RSVP to and remember shared plans: outdoor activities in Bucharest, trips in Romania and abroad, vacations and gaming sessions. Bilingual (Romanian and English), phone first, comfortable on desktop. Hosted on an Oracle Cloud free instance.

- **Plan:** [`docs/PLAN.md`](docs/PLAN.md): decisions, pages, releases (MVP, v2, v3) and data model
- **Designs:** [`docs/design/`](docs/design/): screens and design tokens for both looks
- **Build:** [`docs/BUILD.md`](docs/BUILD.md): tech stack (Django, HTMX, SQLite, Caddy, Docker Compose) and the MVP steps
- **Server:** [`docs/DEPLOY.md`](docs/DEPLOY.md): putting the site on the Oracle server, backups and updates

Status: MVP done and privately tested; next, putting it on the server and revealing it to the friends. v2 and v3 follow.

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

The first makes you the admin. The second prints an invite link; you can also create invites on the Admin page (Me → Admin tools).

To sign in, open <http://localhost:8080>, type your email and press *Email me a sign-in link*. Locally no real email is sent: the email, with the link, appears in the `docker compose up` terminal.

*Continue with Google* appears once you set it up: see [`docs/GOOGLE_SIGN_IN.md`](docs/GOOGLE_SIGN_IN.md).

### Private test with fake data

To see every page filled in, add a fake group (8 members, 16 events around today, answers, guests and two test invites):

```
docker compose exec web python manage.py seed_test_data
```

Run it after `create_owner`: the fake events include answers from you, and some wait for your answer. Dates are counted from today, so to refresh them later run `seed_test_data --reset`: it removes the fake data (members with an `@cumetria.test` address, their events and the two "(test)" invites) and creates it again. `seed_test_data --remove` only removes it, e.g. before the reveal. Either way your own account and events stay.

To see the site as one of them, sign out, type their address (e.g. `ana@cumetria.test`) and open the sign-in link that appears in the `docker compose up` terminal. Worth trying:

- **Ana** organizes several events and has the next birthday; she isn't the admin, so no Admin page.
- **Bogdan** uses the site in English.
- **Ioana** joined two days ago and hasn't answered anything.
- **Mihai** is deactivated: he can't sign in, but his answers still show on past events.

**Login photo:** put the group photo at `static/img/login-photo.jpg` and rebuild; until then the login page shows an empty frame.

## For development (without Docker)

```
pip install -r requirements-dev.txt
DJANGO_DEBUG=true python manage.py migrate
DJANGO_DEBUG=true python manage.py runserver
pytest
```

Romanian texts are in `locale/ro/LC_MESSAGES/django.po`; compile them with `python manage.py compilemessages` (needs GNU gettext). Docker and the GitHub checks do this automatically.
