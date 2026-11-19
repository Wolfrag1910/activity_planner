# Designs

Live canvas: <https://claude.ai/artifact/4wR7dWTwrb1vKdA3yoVHJi>

The `.dc.html` files here are the canvas's source files, kept as a reference for the build. They render only inside the canvas, but the markup and inline styles show exact layout, copy and colours. Colours, fonts and shapes are summarised in [`tokens.md`](tokens.md). Names, events and numbers in the screens are sample data.

## Sunday Picnic (default look)

| File | Screen |
| --- | --- |
| `Main.dc.html` | Phone home |
| `A-Preview.dc.html` | Event quick preview (bottom sheet) with interactive RSVP and reasons |
| `A-Desktop.dc.html` | Desktop home (sidebar, month calendar) |
| `A-Event.dc.html` | Full event page (v2/v3 parts tagged) |
| `A-Calendar.dc.html` | Calendar, month view with filters |
| `A-Propose.dc.html` | Propose an event form |
| `A-Profile.dc.html` | Profile with a working Appearance switch (both looks, light and dark) |
| `A-Login.dc.html` | Login and invite (photo placeholder) |
| `A-Explore.dc.html` | Explore hub |
| `A-Category.dc.html` | Category page (Outdoors) |
| `A-Members.dc.html` | Members |
| `A-Admin.dc.html` | Admin (owner only) |

## Postcard (second look, v2)

| File | Screen |
| --- | --- |
| `C-Home.dc.html` | Phone home |
| `C-Preview.dc.html` | Event quick preview |
| `C-Desktop.dc.html` | Desktop home |

## Other

| File | Screen |
| --- | --- |
| `StyleGuide.dc.html` | Both looks in light and dark, side by side |
| `B-*.dc.html` | Campfire: parked direction, reference for warm dark colours |
| `canvas.json` | Canvas layout index |
