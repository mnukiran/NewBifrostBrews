# Bifrost Brews — Frontend & UI Spec

The visual identity derives from the logo (`assets/logo.png`): a bright, hand-illustrated circular badge — viking longship sailing a rainbow river under a starry navy sky, forest greens, gold knotwork border, runic lettering, tagline "Nectar of the Gods." The site should feel like that logo: **warm, storybook, craft** — not dark-fantasy, not corporate. Think illuminated manuscript meets modern editorial blog.

## Color palette (Tailwind theme tokens)

| Token | Hex | Use |
|---|---|---|
| `parchment` | `#FAF5EA` | Page background |
| `parchment-dark` | `#F0E7D5` | Cards, alternate sections |
| `night` | `#1E2A47` | Header/footer background, primary text on light |
| `night-deep` | `#141D33` | Footer gradient end, code blocks |
| `gold` | `#C9962E` | Primary accent: links, buttons, knotwork details |
| `gold-light` | `#E3B94F` | Hover states, highlights on dark |
| `pine` | `#2F5D3A` | Secondary accent: recipe/success elements, tag pills |
| `timber` | `#7A4A24` | Tertiary: blockquote borders, illustration-adjacent details |
| `rune-red` | `#B33A2B` | Sparing: destructive actions, error states |

**The Bifrost gradient** — the signature element, used *sparingly*:
`linear-gradient(90deg, #B33A2B, #D98A2B, #C9B23A, #3E7C4F, #2E6E8E, #5B4A8A)`
(muted rainbow, harmonized to the palette — not pure RGB rainbow). Uses: 3px top border of the page (fixed under the nav), 2px divider under section headings (short, 64px wide, left-aligned), link underline on hover, admin dashboard chart line. **Never** as a background fill or on buttons.

Contrast: all text/background pairs must meet WCAG AA (4.5:1). `gold` on `parchment` fails for body text — use it for large text, borders, icons only; links in body text use `pine` (or `night` with gold underline).

## Typography (self-hosted via `@font-face`, woff2 only)

| Role | Font | Notes |
|---|---|---|
| Display / headings | **Cinzel** (600, 700) | Roman-carved feel, matches logo lettering without fake-rune kitsch. H1–H3 only |
| Body | **Source Serif 4** (400, 400i, 600) | Warm, highly readable editorial serif, 1.125rem base, line-height 1.7 |
| UI / captions / admin | **Inter** (400, 500, 600) | Buttons, labels, meta lines, admin panel |
| Code | **JetBrains Mono** (400) | Code blocks in articles |

Scale: h1 2.5rem / h2 1.875rem / h3 1.5rem / body 1.125rem / meta 0.875rem. Article text column max-width `65ch`.

## Core components

**Header** — `night` background. Left: logo (48px circle) + "BIFROST BREWS" wordmark in Cinzel, `parchment` color. Right: nav links (Articles, Recipes, About) in Inter, `parchment`, gold underline slide-in on hover; active page underlined gold. Search icon opens an expanding input (Alpine). Sticky, with the 3px bifrost gradient as its bottom edge. Mobile: hamburger → full-width dropdown panel (Alpine collapse).

**Footer** — `night` → `night-deep` subtle gradient. Logo small, tagline *"Nectar of the Gods"* in Cinzel italic gold, nav links repeat, RSS icon, "© 2026 Bifrost Brews". Thin gold knotwork-style border line on top (a repeating SVG pattern, subtle, 40% opacity).

**Article card** — parchment-dark card, 12px radius, soft shadow (`0 2px 8px rgb(30 42 71 / 0.08)`), hover lifts 2px + shadow deepens (150ms ease). Hero image 16:9 WebP with explicit dimensions, title (Cinzel, 1.25rem), summary 2-line clamp, meta line (date · reading time) in Inter `night`/60%, tag pills.

**Recipe card** — like article card plus a **stat strip**: three small badges (OG, FG, ABV%) and a difficulty marker (1–3 drinking-horn icons 🜄 → use a simple SVG horn, not emoji). Style name (e.g. "Cyser") as a small-caps gold label above the title.

**Tag pill** — pine background at 12% opacity, pine text, full-round, 0.75rem Inter; hover → solid pine, parchment text.

**Buttons** — Primary: gold background, night text, 8px radius, medium Inter; hover `gold-light`. Secondary: transparent, 1.5px gold border, night text. Destructive: rune-red equivalents. Focus: 2px `night` outline offset 2px (visible on all interactive elements).

**Ingredient list (recipe detail)** — parchment-dark panel titled "What you'll need" (Cinzel h3 + bifrost divider). Each row: amount+unit right-aligned in a fixed gold-tinted column, item name, optional note in smaller muted text. Alpine checkbox per row for shopping-style check-off (client-side only, no persistence).

**Step timeline (recipe detail)** — vertical line in gold at 30%, nodes as gold circles; each step: "Day N" label (Inter 600 small-caps pine), step title (Cinzel small), description (body serif). Brew day = "Day 0 — Brew Day" highlighted node.

**Stat badges** — pill trio for OG/FG/ABV: label in tiny caps, value in JetBrains Mono 600. ABV badge gets gold border emphasis.

**Search results** — grouped "Recipes" / "Articles", each result: title + FTS snippet with `<mark>` styled gold-at-20% background. Live search: htmx GET on input (300ms debounce) into a dropdown panel; Enter goes to full `/search` page.

**Pagination** — "‹ Older / Newer ›" text links plus page numbers, gold hover underline.

**404 page** — logo, "You've sailed off the Bifrost." + link home. Keep it fun.

## Page layouts

**Home** — Hero section: parchment, large logo left (280px), right: h1 "Brewing the Nectar of the Gods" (Cinzel), one-sentence intro, two buttons ("Read the Guides" primary → /articles, "Browse Recipes" secondary → /recipes). Below: "Latest Brews" (3 recipe cards, grid), "From the Journal" (5 article rows: title + summary + meta), tag cloud strip. Section headings all get the short bifrost divider.

**Article detail** — centered 65ch column. Title (h1), meta line, hero image full column width, body typography (styled headings with anchor links, pine links with gold hover underline, `timber` left-border blockquotes, night-deep code blocks with Pygments theme matching palette). End: tag pills, then "Keep Exploring" — 3 related-by-tag cards.

**Recipe detail** — Title + style label + difficulty horns + stat badge trio at top. Two-column ≥1024px: left 2/3 = ingredients panel then step timeline then narrative body; right 1/3 sticky summary card (batch size, total days, OG/FG/ABV, tags). Mobile: single column, summary card first.

**List pages** — Articles: 12/page card grid (3/2/1 columns at ≥1024/≥640/mobile). Recipes: same grid + filter bar (style select, difficulty select, applied as query params, htmx-swapped grid).

**Admin** — function over flair: Inter throughout, parchment background, night sidebar (Dashboard, Articles, Recipes, Images, Settings, Logout; small logo on top). Dashboard: 4 stat cards, 30-day views line chart (bifrost gradient stroke; render with a tiny inline SVG or vendored uPlot — no Chart.js CDN), top posts table, drafts + scheduled lists. Editor: two-pane split (fields+markdown left, live preview right, stacked on mobile), sticky action bar (Save draft / Preview / Publish, schedule datetime toggle).

## Motion & polish

- Transitions 150ms ease on hover states only; respect `prefers-reduced-motion`
- No scroll-hijacking, no parallax, no autoplaying anything
- Subtle parchment texture allowed as a barely-visible tiled SVG noise (≤2KB, ≤3% opacity) — optional, drop if it hurts perf
- Favicon: logo circle; also provide 180px apple-touch-icon

## Accessibility & quality bar

- Semantic landmarks (`header/nav/main/footer`), one h1 per page, skip-to-content link
- All images require alt text (admin form enforces it)
- Keyboard: full nav + editor operability; visible focus everywhere
- Lighthouse accessibility ≥ 95, performance ≥ 90 on article + recipe pages
