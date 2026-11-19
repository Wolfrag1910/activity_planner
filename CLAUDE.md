# Working on Cumetria

A private, invite-only website for about 9 friends to plan outdoor activities, trips, vacations and gaming sessions. Being built as a surprise; the owner is the only tester until the reveal after v2.

## Read first

- `docs/VISION.md`: why the site exists, how it should feel, judgement calls already made and how the owner likes to work. Read it before making any choice the plan doesn't spell out.
- `docs/PLAN.md`: product decisions, pages, releases (MVP, v2, v3) and data model. Decisions there are settled; don't change behaviour they describe without asking the owner.
- `docs/BUILD.md`: tech stack, server constraints and the MVP steps. Work through the steps in order and tick them off.
- `docs/design/tokens.md` and `docs/design/README.md`: colours, fonts, shapes and the screen mockups (`.dc.html` files show exact layout and copy).

## The owner

Reads Python and Java, does not write HTML, CSS or JavaScript. Explain changes in plain words in pull request descriptions, and keep code readable: clear names, short functions, comments where the reason isn't obvious.

## Conventions

- **Stack:** Django, server-rendered templates, HTMX, plain CSS custom properties, SQLite, Docker Compose, Caddy. No SPA framework, no CSS framework, no build step for front-end assets unless agreed.
- **ARM64:** the server is ARM64. Every dependency and Docker image must support `linux/arm64`.
- **Bilingual:** every user-facing string goes through Django translations, with Romanian and English provided. Dates and times use the Bucharest time zone. Romanian texts live in `locale/ro/LC_MESSAGES/django.po` (written by hand); `core/tests/test_translations.py` fails if a string has no Romanian, and lists the ones to add.
- **Themes:** looks and modes are CSS variable sets selected by attributes on `<html>` (for example `data-look="picnic"`, `data-mode="light"`). Components use variables only, never hard-coded colours. Looks change appearance only, never features.
- **Phone first:** design for 390px wide, then adapt for desktop. Tap targets at least 44px, text contrast at least 4.5:1, real `<button>`/`<a>`/`<label>` elements, no emoji in the interface.
- **Scope:** build only what the current release in `docs/PLAN.md` includes. Ideas outside it go to the owner, not into the code.
- **Tests:** pytest + pytest-django; add tests for every model, permission rule and form. Tests must pass before a pull request is opened.
- **Pull requests:** small, one step or part of a step each, with a plain-language summary of what changed and how to try it locally.
- **Secrets:** never commit `.env` files, keys or OAuth credentials; document required variables in `.env.example`.
- **Server safety:** never change the game servers (Dragonwilds in Docker on UDP 7777/8888, Minecraft Paper on TCP 41882). The website stays under 1 GB RAM.
