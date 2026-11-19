# Build plan

How Cumetria is built and run, and the steps to the first version (MVP). Product decisions live in [`PLAN.md`](PLAN.md); look and feel in [`design/`](design/).

## Tech stack (agreed 19 Nov 2026)

| Piece | Choice | Notes |
| --- | --- | --- |
| Web framework | **Django** (Python) | Server-rendered pages; built-in auth, admin, migrations and translations (RO/EN) |
| Interactivity | **HTMX** + small amounts of plain JavaScript | No SPA framework. RSVP buttons, quick preview, filters update in place |
| Styling | **Plain CSS with custom properties** | One variable set per look and mode, from [`design/tokens.md`](design/tokens.md) |
| Login | **django-allauth** | Google sign-in and emailed sign-in links; signup only through an invite |
| Database | **SQLite** (WAL mode) | One file, backed up with the photos folder. Can move to PostgreSQL later via Django |
| Images | **Pillow** | Resize on upload |
| Web server | **Caddy** | Reverse proxy with automatic HTTPS |
| App server | **Gunicorn** | Behind Caddy |
| Runtime | **Docker Compose** | All images must support **linux/arm64** |
| Tests | **pytest + pytest-django** | Run in GitHub Actions on every pull request |

## Server facts (snapshot 19 Nov 2026)

- Oracle Ampere A1 (`VM.Standard.A1.Flex`), 4 OCPUs, 24 GB RAM, **ARM64**, Ubuntu 20.04.6 LTS.
- About 18 GiB RAM and 39 GB disk free. No swap.
- Already running, and must stay available: **Dragonwilds** (Docker Compose, UDP 7777 and 8888) and **Minecraft Paper** (native Java under GNU screen, TCP 41882, `-Xmx4G`).
- Docker and Compose installed. Nothing listens on 80/443 yet.

The website should stay well under 1 GB RAM. Do not change or restart the game servers' setups.

### Before the site goes public (Launch phase)

- [ ] Keep Ubuntu 20.04 patched: enable **Ubuntu Pro** (free for personal use) for security updates, or plan an OS upgrade separately from the game servers.
- [ ] Open TCP 80 and 443 in the **Oracle security list** and in **Ubuntu's iptables rules** (Oracle images block them by default).
- [ ] Get a domain name (research task) and point it at the server.
- [ ] Nightly backup of the SQLite file and the photos folder to somewhere off the server.

## How we work

1. Claude Code writes the code in this repository in **small pull requests**; the owner reviews and merges.
2. The owner runs the site locally with `docker compose up` and tests it with fake member accounts (the private test).
3. Deploy: on the server, pull `main` and run `docker compose up -d --build` (images build natively on ARM64).

## MVP steps

Each step is one or a few pull requests. Every step keeps the site runnable and adds tests for what it adds.

- [x] **1. Skeleton.** Django project, settings from environment variables, SQLite, Docker Compose (web + Caddy), static files, RO/EN translation setup, base layout (phone bottom bar, desktop sidebar, top bar with bell and language switch), theme CSS for Sunday Picnic Light, GitHub Actions running tests, README section on running locally.
- [ ] **2. Members and access.** Custom member model (name, photo, birthday, language, look, light/dark choice, role, active). Invite links created by the admin (single use, cancellable). Google and email-link login through allauth, only via an invite. Profile page (with Appearance stored, even if only Sunday Picnic Light is styled), Members page, Admin page (invites, deactivate).
- [ ] **3. Events.** Event model and categories, Propose/Edit/Cancel form (organizer or admin), event page, RSVP Going/Maybe/No with quick-pick reasons and note, +1 guests with optional names counting toward spots, "answer by" deadline.
- [ ] **4. Browsing.** Home page (Today/Next up, category shortcuts, Upcoming, Waiting for your RSVP), quick preview (bottom sheet on phone, side panel on desktop), Calendar (month and list, category filters, multi-day bars), Explore, category pages.
- [ ] **5. Polish.** Desktop layouts of all pages, full Romanian translation pass, accessibility pass (tap targets, contrast, keyboard), empty states.
- [ ] **6. Private test kit.** Command that seeds fake members and events; a deployment guide for the Oracle server (firewall, Caddy, backups). Do not launch publicly: the reveal comes after v2.
