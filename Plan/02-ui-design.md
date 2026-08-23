# UI Design Style Guide

## Design principles
1. **Minimal but not bare.** Generous whitespace and few elements per
   screen, but real typographic hierarchy and one deliberate accent color —
   not just black-on-white unstyled HTML.
2. **Content-first.** The site is a knowledge base + forum; text is the
   product. Layout should get out of the way (single readable column for
   long-form content, no busy sidebars).
3. **Fast and light everywhere.** No large hero images, no JS frameworks,
   fonts limited to two self-hosted subset woff2 families. This isn't just
   aesthetic — the server is a phone, so small payloads matter too. The one
   deliberate exception is YouTube embeds, and even those load as a light
   thumbnail facade until clicked (see "Video embed" below).
4. **Consistent, small component set.** Reuse the same card, button, and
   nav patterns everywhere rather than inventing new ones per page.

## Color
Dark-friendly, neutral-first palette with one accent. Exact hex values are
a starting proposal — tune once you see it rendered.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#FAFAF9` | `#111113` | page background |
| `--surface` | `#FFFFFF` | `#1A1A1D` | cards, nav bar |
| `--text` | `#1A1A1A` | `#EDEDED` | body text |
| `--text-muted` | `#6B6B6B` | `#9A9A9A` | secondary text, metadata |
| `--border` | `#E5E5E3` | `#2A2A2E` | dividers, card borders |
| `--accent` | `#5B5BD6` (indigo) | `#8A8AF0` | links, buttons, active states |

Support both light and dark via `prefers-color-scheme` — cheap to add up
front, and phone-hosted sites get viewed at odd hours.

## Typography
- **Body**: a system-first stack (`-apple-system, Segoe UI, Inter, sans-
  serif`) or self-hosted Inter woff2 (recoverable from the old project via
  git history, or re-fetched) at **16px base**, 1.6 line-height for
  long-form reading. Use `font-display: swap` so text never blocks on the
  font.
- **Headings**: same family as body, just heavier weight — avoid mixing in
  a second display typeface; "minimalistic" means one voice, not two fonts.
- **Code/monospace** (for any technical course notes): JetBrains Mono
  (same recovery route) for inline code and snippets.
- Scale: 14 / 16 / 20 / 28 / 40px — five sizes is enough for this site's
  page depth (nav/meta, body, subhead, page title, hero-ish title).

## Layout
- Max content width ~680–760px for reading (articles, course notes, forum
  posts) — wider (~1000px) for grid views (course list, category list).
- Top nav: logo/wordmark left, 3–4 links right (Home / Courses / Forum /
  About). Collapses to a simple menu button on narrow viewports (Alpine.js
  toggle, no hamburger animation flourish needed).
- No footer clutter — a single line (copyright/attribution + maybe a link
  back to Assets/source material once that's public) is enough.

## Components (initial set)
- **Button**: solid accent background for primary action, ghost/outline for
  secondary. One size unless a page truly needs two.
- **Card**: used for course list items and forum thread previews — surface
  background, 1px border, small radius (6–8px), modest padding, hover =
  subtle border-color shift to accent (no shadow-heavy "lift" effects).
- **Nav pill / tag**: small rounded label for course tags/forum categories,
  muted background, muted text, no border.
- **Empty/"coming soon" state**: since Phase 1 ships before real content
  exists, design one clean empty-state pattern now (icon-free, just a short
  muted sentence + optional link) rather than leaving raw blank pages.
- **Video embed** (Phase 2): responsive YouTube embed that plays in-page.
  A wrapper with `aspect-ratio: 16 / 9; width: 100%; border-radius: 8px;
  overflow: hidden` fills the content column on any screen. Default render
  is a **facade**: the video's `hqdefault.jpg` thumbnail + a centered play
  button styled with the accent color; clicking swaps in the real
  `youtube-nocookie.com` iframe with autoplay, so it starts immediately and
  plays right there in the page. This keeps un-clicked pages light and
  makes every embed look consistent. Give the facade a visible focus state
  and `aria-label="Play video: <title>"` for keyboard/screen-reader users.

## Admin editor (Phase 2)
The editor is an internal tool but should still feel tidy: same design
tokens, monospace (JetBrains Mono) textareas for the HTML/CSS/JS fields,
side-by-side (stacked on mobile) live preview pane refreshed via htmx, a
clear Draft/Published toggle, and an obvious unsaved-changes indicator.
Admin-authored content renders inside a `.course-content` container that
inherits the site's typography by default, so a course page with zero
custom CSS still looks properly designed.

## Motion
Minimal: short (~120–150ms) opacity/color transitions on hover/focus only.
No page-transition animations, no scroll-triggered effects — consistent
with the "gets out of the way" principle and keeps JS to near-zero.

## Accessibility baseline
- Color contrast meets WCAG AA for text/background pairs above (verify the
  accent-on-bg link color once finalized).
- Visible focus states (don't rely on browser default alone, but don't
  remove it either — style `:focus-visible`).
- Semantic HTML first (`nav`, `main`, `article`, `button` vs `div` soup) —
  htmx/Alpine both work fine with real semantic markup.
