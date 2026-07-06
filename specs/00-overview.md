# Bifrost Brews — Project Overview

## What this is

A blog and recipe site about mead-making and other fermented/alcoholic beverages, at **bifrostbrews.co**. Tagline: *"Nectar of the Gods."* Norse/Bifrost branding (logo: viking longship sailing a rainbow river, gold knotwork border).

This spec set is written for an AI coding agent. Build and run everything **locally on a laptop**. Deployment (to a postmarketOS phone server) is a separate future project — do NOT add deployment tooling, Docker, or cloud config. The only deployment-driven requirement is that the app stays **lightweight**: it must eventually run comfortably on a phone with limited RAM.

## Hard constraints

1. **Python backend** — FastAPI, served by uvicorn.
2. **SQLite** database — single file, via SQLAlchemy 2.x. No Postgres/MySQL, no external DB server.
3. **Server-rendered HTML** — Jinja2 templates. No React/Vue/SPA. No client-side routing.
4. **Light JS only** — htmx + Alpine.js (~20KB total) for interactivity. No bundler beyond the Tailwind CLI.
5. **Tailwind CSS** compiled at build time via Tailwind CLI. No CDN runtime, no CSS-in-JS.
6. **Single admin user** — the site owner. No public registration, no multi-user roles.
7. All content, images, and data live on local disk (SQLite file + uploads folder).

## V1 scope

| Area | In v1 |
|---|---|
| Content | **Articles** (prose, markdown) and **Recipes** (structured: ingredients, gravities, ABV, timeline) |
| Discovery | Full-text search, tag filtering, tag pages |
| Admin | Login, markdown editor with live preview, drafts, scheduled publishing, image uploads, per-post view counts |
| SEO | Semantic HTML, meta/OpenGraph tags, sitemap.xml, RSS feed |

## Explicitly out of scope for v1 (design so they can be added later, but do not build)

- Brewing calculators (ABV, target gravity, priming sugar) — likely v2
- Comments, newsletter signup, brew log/batch journal, glossary
- Any deployment/hosting setup beyond `uvicorn` on localhost

## File map

| File | Contents |
|---|---|
| `00-overview.md` | This file — scope, constraints, build order |
| `01-architecture.md` | System design, directory layout, tech decisions, local dev setup |
| `02-backend-spec.md` | Database schema, routes, auth, scheduling, analytics |
| `03-frontend-ui-spec.md` | Design system (logo-derived), components, page layouts |

## Assets

- `assets/` — the Bifrost Brews logo (circular badge) in ready-to-use sizes. Copy into `app/static/img/` during setup:
  - `logo-web.webp` (512px) — use in header, hero, footer. Do NOT ship the 4.8MB `logo.png` original to browsers.
  - `logo-512.png` — OpenGraph fallback image
  - `apple-touch-icon.png` (180px), `favicon-32.png` — favicons
  - Never generate a substitute logo; if a size is missing, resize from `logo.png`.

## Build order

1. Project skeleton, dependencies, config, Tailwind pipeline (per `01-architecture.md`)
2. Database models + migrations seed (per `02-backend-spec.md` § Data model)
3. Public routes with basic templates (home, article, recipe, tag, search)
4. Admin: auth → CRUD for articles/recipes → image uploads → scheduling → view counts
5. Apply the full design system (per `03-frontend-ui-spec.md`)
6. SEO: meta tags, sitemap, RSS
7. Seed with 2–3 sample articles and 2 sample recipes (mead-themed placeholder content, clearly marked as samples)
8. Verify the acceptance checklist below

## Acceptance checklist

- [ ] `make dev` (or the two documented commands) brings the site up at `http://localhost:8000`
- [ ] Admin can log in, create a draft, preview it, publish it, and see it live
- [ ] A recipe renders with ingredient list, stat badges (OG/FG/ABV), and step timeline
- [ ] Search returns matching articles and recipes; tag pages filter correctly
- [ ] Scheduled post with future date is hidden publicly, appears after its time passes
- [ ] Uploaded images are resized/served locally and display in posts
- [ ] View counts increment for public visits, not for the logged-in admin
- [ ] Lighthouse: 90+ performance and accessibility on the article page
- [ ] Total JS shipped to readers < 50KB gzipped
