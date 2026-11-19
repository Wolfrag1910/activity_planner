# Design tokens

Two looks, each with a light and a dark version. Every page uses the same components; only these values change. **Sunday Picnic Light is the default** (also used on the login screen). Postcard and dark mode ship in v2, but the theme system that switches between them is part of the MVP.

## Colours

| Token | Sunday Picnic Light | Sunday Picnic Dark | Postcard Light | Postcard Dark |
| --- | --- | --- | --- | --- |
| Background | `#F7F1E8` | `#1C1714` | `#FBEFD9` | `#2B2119` |
| Surface (cards) | `#FFFCF7` | `#27201B` | `#FFF8EC` | `#3A2E23` |
| Text | `#2B211A` | `#F5ECE1` | `#2A1E14` | `#FBEFD9` |
| Muted text | `#6E5F52` | `#BBA996` | `#6B5A48` | `#D2C1A8` |
| Accent (primary buttons) | `#B4532A` | `#E07A4F` | `#C8402A` | `#F0674E` |
| Text on accent | `#FFFFFF` | `#1C1714` | `#FFFFFF` | `#1A120C` |
| Lines / outlines | `#E6DACB` | `#3B312A` | `#2A1E14` | `#0E0A07` |

Postcard Dark keeps **near-black outlines and hard shadows** (like Postcard Light), on lighter warm-brown surfaces. Do not use light or accent-coloured outlines or shadows there: they looked wrong in review.

## Category colours (chip background / chip text)

| Category | Sunday Picnic Light | Sunday Picnic Dark | Postcard Light | Postcard Dark |
| --- | --- | --- | --- | --- |
| Outdoors | `#E3ECD9` / `#2F4D21` | `#2C3A22` / `#B5D69B` | `#CFE3B8` / `#2D4E1C` | `#2F4523` / `#CFE3B8` |
| Trips | `#DCE7F1` / `#1E4566` | `#1F3346` / `#A9CBEB` | `#C9DDF0` / `#1D4568` | `#1F3A55` / `#C9DDF0` |
| Vacations | `#F6E3C4` / `#6E4310` | `#43321A` / `#EDC88A` | `#F6CFA8` / `#7A3D0D` | `#5A3415` / `#F6CFA8` |
| Gaming | `#E8E0F2` / `#45306B` | `#33284A` / `#CDBBF2` | `#DCCDF0` / `#47306F` | `#3A2B57` / `#DCCDF0` |

Solid category colours (calendar dots, Postcard ticket stubs): Outdoors `#4F7A3A` / `#3F6B2A`, Trips `#2F6690` / `#24557F`, Vacations `#C08320` / `#9A4E12`, Gaming `#6B4C9A` / `#563B87` (Sunday Picnic / Postcard). Birthdays use the accent colour.

## Type

| | Sunday Picnic | Postcard |
| --- | --- | --- |
| Headings | Fraunces 600/700 (serif) | Bricolage Grotesque 800 |
| Body | Inter 400/500/600 | DM Sans 400/500/700 |

All four are Google Fonts. Fallbacks: Georgia for Fraunces, system sans for the rest.

## Shapes

| | Sunday Picnic | Postcard |
| --- | --- | --- |
| Card radius | 18px | 14px |
| Button radius | 14px | 12px |
| Card border | 1px, lines colour | 2px, outline colour |
| Card shadow | none | hard `4px 4px 0` in outline colour |
| Primary button shadow | soft, accent-tinted (light only) | hard `3px 3px 0` in outline colour |
| Propose (+) button | circle | rounded square |

## Rules

- Tap targets at least 44px. Text contrast at least 4.5:1.
- No emoji in the interface; icons are simple stroke icons.
- Real `<button>`, `<a>`, `<input>` + `<label>` elements.
