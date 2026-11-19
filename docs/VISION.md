# Vision: what the plan doesn't say

`PLAN.md` says **what** to build. This file says **why** and **how it should feel**, plus the judgement calls made along the way, so anyone picking up the work (a new chat, Claude Code) makes the same calls the owner would. Written 19 Nov 2026 at the end of the design phase.

## Why Cumetria exists

A close group of about 9 friends in Bucharest organizes everything today through WhatsApp events and Discord events. Plans get lost in chats, nobody knows who is really coming, and memories end up scattered across phones. Cumetria is their own place: propose something, see who's in, and keep the photos and stories afterwards.

It is **a gift**. The owner is building it as a surprise and will reveal it after v2. The first time the friends open it, it should feel like it was made *for them*, not like a generic app. They are smart, they care, and after the reveal they will flood the backlog with feedback. Build so that taking their ideas on board is easy.

## How it should feel

- **Warm and simple, never corporate.** Cream, terracotta, serif headings; friendly copy ("You're in", "One plan tonight", "Who's coming"). The group is "cool and vibe-y".
- **Between minimal and decorated.** Some friends dislike strict minimalism; nobody wants clutter. Personality comes from colour, type, rounded shapes and real photos, not from ornaments.
- **No "AI slop".** The owner rejected a hand-drawn SVG landscape on the login screen for looking generic; it became a placeholder for a real group photo. Avoid gradient washes, decorative blobs, stock illustrations, emoji and filler copy. When in doubt, leave space or use a real photo slot.
- **Phone first, desktop for real.** Friends use phones; the owner uses a PC and wants the desktop to feel designed, not stretched.
- **The home page does most of the work.** Most visits should end on the home page: what's today, what needs my answer, what's next.
- **One tap where it matters.** RSVP from the card or the quick preview; reasons are quick picks, not forced typing.

## The two looks

Sunday Picnic (default) and Postcard are both loved; the owner could not choose, so members choose. They differ only in appearance. Postcard's personality is the near-black outline plus hard offset shadow; in dark mode it keeps near-black outlines (light outlines and accent-coloured shadows were tried and looked wrong). Campfire (dark, amber) was parked and serves as the reference for warm dark colours.

## Judgement calls already made

- Voting is optional; organizers can publish directly. The organizer, not a threshold, decides when interest is enough.
- Reasons for Maybe/No are visible to everyone: this is a trusting group of friends, transparency helps plan.
- Guests (+1) are welcome, including younger siblings; a guest's name is optional so surprise guests stay a surprise.
- Photos: upload only, no download button, admin can delete. The album opens when the event starts.
- Costs are settled per event; nobody wants running debts between friends.
- Only Discord for notifications; WhatsApp was dropped as not worth the cost and ban risk.
- Invite links are sent personally by the owner; the site doesn't email invites.

## How the owner likes to work

- **Asks before big steps.** Present the plan or options with honest trade-offs and a recommendation, then wait for a yes. Small, obvious fixes don't need a question.
- **Reviews carefully.** He checks designs against the plan and spots inconsistencies (missing pages, mismatched numbers). Self-check before showing work.
- **Drops ideas as they come.** Capture every idea in the backlog with who suggested it and a proposed release; never silently drop or silently build one.
- **Reads Python, not web code.** Explain changes in plain words; keep code readable.
- **Records decisions.** Every settled decision goes into `PLAN.md` (and the living plan doc) the same day.

## What to protect

- The game servers on the Oracle box (Dragonwilds, Minecraft) are the group's other shared space. Never disturb them.
- Privacy: invite-only, no public pages, no tracking, no third-party analytics.
- The surprise: nothing should notify or reach the friends before the reveal.
