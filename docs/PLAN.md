# Cumetria: project plan

Cumetria (working name) is a private, invite-only website where about 9 friends propose, vote on, RSVP to and remember shared plans: outdoor activities in Bucharest, trips in Romania and abroad, vacations and gaming sessions. It is being built as a surprise, so the owner is the only tester until the reveal.

This file is the build-ready copy of the living plan doc, exported on 19 Nov 2026:
<https://claude.ai/artifact/TTsDvmmh2WPz1Rdv4UFeXE> (decision history and change log live there).
Designs: <https://claude.ai/artifact/4wR7dWTwrb1vKdA3yoVHJi> (source files in [`docs/design/`](design/)).
Keep both in sync: when a decision changes, update this file and the doc.

## Phases

1. **Discovery** (done)
2. **Site plan** (done)
3. **Design direction** (done)
4. **Build in slices** (current): MVP, then v2, then v3. See [`BUILD.md`](BUILD.md).
5. **Private test**: the owner tests each release with fake member accounts.
6. **Launch**: hosting, domain, inviting friends **after v2**. From then on, friends' ideas go into the backlog.

## Releases at a glance

| Release | Contents | Audience |
| --- | --- | --- |
| MVP | Invites and login, profiles, members, propose/edit/cancel events (published directly), RSVP with reasons and +1 guests, home, calendar, Explore, 4 category pages, event page with quick preview, admin page, RO/EN, phone and desktop layouts, theme system with the Sunday Picnic look | Owner only (private test) |
| v2 | Interest voting and polls, bell notifications, Discord notifications, day-before reminders, comments, photo albums, named reviews, birthdays on the calendar, calendar subscribe link, Postcard look, dark mode, ideas and feedback box | The reveal to friends |
| v3 | Cost splitting with "I paid" confirmation and costs overview, places map, weather forecast, past events archive | After the reveal |

## Decisions (41)

### Accounts and access
- Users have accounts; the site is **invite-only** (about 9 people, no public sign-up).
- Login with **Google or an emailed sign-in link**; no passwords.
- **Only the admin invites.** The site creates a personal, single-use invite link; the admin sends it personally (WhatsApp or Discord). The site does not email invites.
- One **admin** (the owner). Only an event's **organizer** can edit or cancel it; the admin can step in on any event and can delete any photo.
- A **deactivated member** can't log in, but their past RSVPs, photos and comments stay.

### Language, devices, looks
- Site in **Romanian and English**, switchable per user; built in from day one.
- **Phone first**, but fully comfortable on desktop (the owner mostly uses a PC).
- Two **looks**, chosen per member in Profile > Appearance and saved to the account: **Sunday Picnic** (default, also used on the login screen) and **Postcard**.
- Looks change **only appearance, never features**: every page shows the same content in both.
- The **theme system** is built into the MVP; Postcard ships in v2.
- **Dark mode** for both looks (Light / Dark / Match my phone), in v2.
- "Cumetria" is a placeholder name and does not drive the look.
- The login screen shows a real **group photo** chosen by the owner (placeholder until then).

### Events
- The proposer chooses: **publish directly** as an official event, or **open it to a vote** first (v2).
- Voting: **the organizer decides** when there is enough interest (a number of votes, regardless of any deadline), then confirms the event or cancels it.
- RSVP is **Going / Maybe / No**. Maybe and No open **quick-pick reasons** (Working, Out of town, Not feeling it, Other) plus an **optional note**.
- **Everyone can see** who answered Maybe or No, and their reason.
- RSVPs can include **+1 guests who are not members** (e.g. younger siblings). Guests need no account, **count toward max spots**, and their **name is optional** (blank = surprise guest).
- **"Answer by" (RSVP deadline) is optional**; left empty, people can answer until the event starts.
- Tapping an event card anywhere opens a **quick preview** (bottom sheet on phone, side panel on desktop) with essentials, RSVP buttons and an **Open event** button.
- **Reviews are named**: thumbs up or down plus optional text, after the event (v2).

### Photos
- Photos can be **uploaded but not downloaded** (no download button); the admin can delete photos.
- **No upload limits**; photos are resized on upload.
- An event's album **opens when the event starts**; only people who went can add photos.

### Costs (v3)
- Costs in **EUR and RON**, any custom cost (trip budget, a meal, anything): the payer adds people and what each owes.
- Each cost uses **one chosen currency, with the other in parentheses**, e.g. `200 RON (40 EUR)`.
- Exchange rate: **National Bank of Romania (BNR) daily rate, fixed when the cost is added.**
- **Settled per event**; nothing carries over between events.
- The person who owes taps **"I paid"**, then the collector **confirms** (no proof needed).

### Calendar, home, notifications
- **One shared calendar**, colour-coded by category, filtered on each category page.
- **Birthdays** come from profiles and show the day and the age.
- **Calendar sync is one-way**: a personal subscribe link (Google, Apple, Outlook).
- The **home page** should cover most of the "get informed" need.
- **Category shortcut buttons** on the home page, each with its count of upcoming events.
- **Map pins** are added automatically from event locations (v3).
- Notifications go to **Discord only** (WhatsApp dropped) plus the in-site bell (v2).

### Build and hosting
- **Build in slices**: MVP first, then v2 and v3.
- Host on the owner's **Oracle Cloud free instance** (it already runs game servers; check spare CPU, memory and disk).
- **Database on the same server**, if it costs nothing (to be verified).
- **Reveal to friends after v2.**

## Event lifecycle

```
Proposed ──► Open to voting? ──yes──► Voting ──enough interest──► Confirmed ──► Done
                  │                     └──not enough──► Dropped (cancelled)
                  └──no: publish directly ──────────────► Confirmed
```

**Categories:** Outdoors (Bucharest) · Trips (Romania and abroad) · Vacations · Gaming · Birthdays (automatic, from profiles).

### What an event holds

| Field | Applies to | Notes |
| --- | --- | --- |
| Title, description, category, organizer | All | |
| Start date and time; end time or date range | All | Trips and vacations last several days |
| Place and meeting point, map link and coordinates | In-person events | Feeds the places map (v3) |
| Open to voting or publish directly | All | Chosen by the proposer |
| Polls | Any event (v2) | Date, place, game, destination or custom question; can also stand alone |
| RSVP deadline ("answer by"), maximum spots | Optional | Guests count toward spots |
| Estimated cost / costs | Optional (v3) | |
| What to bring | Outdoors, trips | Free text in the description for now |
| Game, platform, online or in person, Discord link | Gaming | |
| Weather forecast | Outdoor events (v3) | Shown when the date is within forecast range |
| Comments, photos, reviews | All (v2) | |

## Pages (13; 10 in the MVP)

| Page | What it shows | Who sees it | Release |
| --- | --- | --- | --- |
| Login and invite | Accept invite link, sign in (Google or email link), choose RO or EN | Invited people | MVP |
| Home | Today (or Next up), category shortcuts, Upcoming, Waiting for your RSVP; later Needs your vote and birthdays (v2) | Members | MVP |
| Calendar | Month and list views, colour per category, filter chips; later birthdays and subscribe link (v2) | Members | MVP |
| Explore | Four category cards with their next event; links to Memories (v2), Members, Ideas and feedback (v2) | Members | MVP |
| Category page (×4) | Upcoming, ideas open to a vote (v2), filtered calendar, past events | Members | MVP |
| Event page | Details, place and map link, your answer and guests, who's coming with reasons; later poll, comments, photos, reviews (v2), costs and weather (v3) | Members | MVP |
| Propose or edit event | Category, title, publish now or vote first (v2), dates, place, details, spots, answer by; later add poll (v2), add cost (v3) | Members; edit by organizer or admin | MVP |
| Members | Everyone with photo and birthday; next birthday highlighted | Members | MVP |
| Profile | Name, photo, birthday, language, appearance (look and dark mode), my upcoming; later calendar link (v2), what I owe and am owed (v3) | Members | MVP |
| Admin | Create and cancel invite links, deactivate members, reminder of edit/cancel and photo-delete powers | Owner only | MVP |
| Notifications | The bell's list of updates, unread first | Members | v2 |
| Memories | All photo albums (v2); places map and past events archive (v3) | Members | v2 |
| Costs overview | Open costs across events: what I owe, what I'm owed, "I paid" and confirm buttons | Members | v3 |

Discord is not a page: from v2 the site posts updates to a channel in the group's server.

**Navigation.** Phone: bottom bar with Home, Calendar, a raised **+** (propose), Explore, Me. Desktop: left sidebar with everything; wide pages put the calendar beside the event list. Both: bell and RO/EN switch at the top right.

**Bell triggers (v2):** new event or proposal; a change to an event you RSVP'd to (date, time, place, cancellation); a vote or poll you joined closes, with result; replies to your event or comment; new photos on an event you attended; reminder the day before an event you're going to. The same updates post to Discord.

## What the site stores

| Record | What it holds | Linked to | Release |
| --- | --- | --- | --- |
| Member | Name, photo, birthday, language, look and light/dark choice, role (member or admin), login identity, active or not | Everything a person does | MVP |
| Invite | Personal single-use link, created by the admin, used or not | Becomes a member when accepted | MVP |
| Event | Title, category, description, start and end, place and coordinates, max spots, RSVP deadline, status (proposed, voting, confirmed, cancelled, done) | Organizer | MVP |
| RSVP | Going, Maybe or No, quick-pick reason, optional note | Member, event | MVP |
| Guest | Optional name; takes one spot | The RSVP that brought them | MVP |
| Interest vote | Who is interested | Member, event | v2 |
| Poll | Question, options, who picked what | Event (optional), members | v2 |
| Comment | Text, time | Member, event | v2 |
| Photo | Resized image file, uploader, time | Event, member | v2 |
| Review | Thumbs up or down, optional text | Member, event | v2 |
| Notification | What happened, link, read or unread | Member; also posted to Discord | v2 |
| Cost | Title, total, currency, exchange rate fixed when added | Event, the member who paid | v3 |
| Cost share | Amount owed, status (owed, "I paid", confirmed) | Cost, the member who owes | v3 |

Birthdays come from member profiles and map pins from event locations, so neither needs its own record.

## Design

See [`docs/design/README.md`](design/README.md) for the screens and [`docs/design/tokens.md`](design/tokens.md) for colours, fonts and shapes of both looks in light and dark.

Still to design, before the release that needs them:
- [ ] Desktop layouts of the inner pages (during the MVP build, following the desktop home)
- [ ] v2: organizer's view of a proposal (interest count, Confirm or Cancel)
- [ ] v2: notifications panel behind the bell
- [ ] v2: review after an event
- [ ] v2: photo album and Memories page
- [ ] v2: create a poll; add a guest; ideas and feedback box
- [ ] v3: add a cost, the collector's confirm view, costs overview, places map

## Hosting and tech notes

- Runs on the owner's **Oracle Cloud free instance** (ARM64). **Tech stack (agreed 19 Nov 2026):** Django + HTMX + plain CSS variables, SQLite, Caddy for HTTPS, Docker Compose. Details and MVP steps: [`BUILD.md`](BUILD.md).
- **Database:** SQLite on the same server, so it costs nothing extra; nightly automated backup off the server.
- **Photos** stored outside the database (server disk or Oracle object storage; free allowance to verify), resized on upload.
- **Discord**: posting through a channel webhook is simple and free; a bot (e.g. RSVP buttons in Discord) is a later idea.
- **Calendar sync**: a personal iCal subscribe link per user.
- **Weather**: a free forecast service with no paid plan (to verify at build time).
- **Domain and HTTPS**: the owner is looking for a free domain; HTTPS is required.

## Backlog ideas not scheduled

- Carpool: drivers and free seats (Idea)
- WhatsApp notifications (Cut, 18 Nov 2026)

## Open questions (research tasks for Claude before launch)

- [x] **Database cost:** answered 19 Nov 2026. SQLite inside the existing free server costs nothing extra.
- [ ] **Domain:** free or very cheap options, and how each works with HTTPS on the Oracle server.
