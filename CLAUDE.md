# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository currently contains **only specs** (`specs/00-overview.md` through `specs/03-frontend-ui-spec.md`) and logo assets (`specs/assets/`). No application code exists yet. The specs are written for an AI coding agent to implement from scratch — read all four before writing code, since they cross-reference each other (e.g. the data model in `02-backend-spec.md` depends on directory layout in `01-architecture.md`).

Follow the **build order** in `specs/00-overview.md` § Build order: skeleton/config/Tailwind → DB models → public routes → admin (auth → CRUD → uploads → scheduling → view counts) → design system → SEO → seed content → acceptance checklist.

## What this is

Bifrost Brews — a mead-making/fermented-beverage blog+recipe site (bifrostbrews.co). Built to run locally on a laptop; deployment to a postmarketOS phone is a separate future project — **do not add Docker, cloud config, or deployment tooling**. The only deployment-driven constraint that matters now is keeping the app lightweight enough to eventually run on a phone with limited RAM (see Performance budget below).

## Hard constraints (do not deviate)

- **FastAPI** (Python 3.12+) + **uvicorn**. Server-rendered **Jinja2** HTML only — no React/Vue/SPA, no client-side routing.
- **SQLite** via **SQLAlchemy 2.x**, single file. No Postgres/MySQL/external DB server.
- **htmx + Alpine.js** only for interactivity (~20KB total, vendored locally, not CDN). No other JS framework/bundler beyond the Tailwind CLI.
- **Tailwind CSS v4** compiled via the standalone CLI at build time. No CDN runtime, no CSS-in-JS.
- **Single admin user** (site owner). No public registration or multi-user roles.
- All content/images/data on local disk: SQLite file + `data/uploads/`.
- Explicitly **out of scope for v1** (design so they're addable later, but don't build): brewing calculators, comments, newsletter signup, brew log/batch journal, glossary.

## Commands (per `specs/01-architecture.md` § Local dev — set these up if missing)

```
uv sync                          # install deps
python scripts/set_password.py   # create .env admin credentials
alembic upgrade head              # run migrations
python scripts/seed.py            # optional sample content
tailwindcss -i styles/input.css -o app/static/css/site.css --watch   # terminal 1
uvicorn app.main:app --reload     # terminal 2 -> http://localhost:8000
```

A `Makefile`/`justfile` should provide `make dev`, `make css`, `make test`, `make seed`. Tests run via `pytest` (see Testing below).

## Architecture

Directory layout (see `specs/01-architecture.md` for the full tree):

```
app/main.py          # FastAPI app factory, middleware, startup
app/config.py        # pydantic-settings, reads .env
app/db.py            # engine, session dependency
app/models.py        # SQLAlchemy models
app/routers/         # public.py, admin.py, auth.py, feeds.py
app/services/        # content.py (queries), markdown.py, images.py, analytics.py
app/templates/       # base.html, partials/, public/, admin/
app/static/          # compiled css, vendored htmx/alpine, img
alembic/             # migrations
scripts/seed.py       # sample content seeder
```

Key architectural decisions that shape how code should be written here:

- **Markdown is rendered at save time**, not per-request. `body_md` → sanitized `body_html` is cached in the DB and re-rendered only on edit. Never render markdown in a hot request path.
- **No background worker/scheduler.** "Is a post live?" is just the predicate `status != 'draft' AND published_at <= now()`, applied identically by every public route, RSS, and the sitemap. Scheduled posts become visible automatically once real time passes it — don't build a cron/worker for this.
- **Articles and recipes are separate tables** (`posts`, `recipes`) sharing publishing fields (status/published_at/slug/etc.), not a shared polymorphic table. Recipes add structured brewing data (`ingredients_json`, `steps_json`, OG/FG/ABV) plus an optional narrative `body_md`.
- **Search is SQLite FTS5** (`search_index` virtual table), kept in sync by explicit rebuild-on-save/publish/unpublish in the service layer — no DB triggers.
- **Images**: validate → strip EXIF → resize (max 1600px + 400px thumb) → re-encode to WebP at upload time; originals are never served. Stored at `data/uploads/YYYY/MM/{slug}-{shortid}.webp`.
- **Slug changes** after publish write an entry to a `redirects` table, checked in the 404 handler for a 301.
- **SQLite pragmas**: WAL mode, `busy_timeout=5000`, `foreign_keys=ON` — set on connect. One writer (admin) + many readers is the expected access pattern.
- **Analytics** are middleware-based view counting (`view_count` + `daily_views`) on public detail routes, skipped for admin sessions and known bots. No cookies or IP storage for readers.
- Timestamps stored as UTC ISO strings; rendered in `SITE_TZ` from config.

Full data model, routes, and the publishing state machine are in `specs/02-backend-spec.md`. Full design system (colors, type, components, page layouts) is in `specs/03-frontend-ui-spec.md` — the palette and Cinzel/Source Serif 4/Inter/JetBrains Mono type roles are derived from the logo and should be implemented as Tailwind `@theme` tokens, not ad-hoc values.

## Performance budget (phone-aware — treat as hard requirements, not aspirations)

- Reader-facing JS < 50KB gzipped total; CSS < 30KB gzipped.
- No N+1 queries (eager-load tags); no per-request markdown rendering.
- Images always WebP with explicit width/height attributes (no layout shift).
- Lighthouse performance ≥ 90 and accessibility ≥ 95 on article/recipe pages.

## Security summary (from `specs/02-backend-spec.md`)

- Pydantic validation on every form/endpoint; slugs constrained to `^[a-z0-9-]{1,80}$`.
- Uploads: whitelist jpeg/png/webp, ≤10MB, verify magic bytes via Pillow, always re-encode, strip EXIF.
- Rendered HTML sanitized with `nh3`; Jinja2 autoescape on — never use `|safe` except on the already-sanitized `body_html`.
- Argon2 password hashing, signed session cookies (`itsdangerous`), CSRF token on mutating admin forms, login rate-limited (5 failures / 15 min / IP).
- Security headers middleware: `X-Content-Type-Options`, `X-Frame-Options: DENY`, basic CSP.

## Testing

Minimum pytest coverage per `specs/02-backend-spec.md` § Tests: auth (bad password, rate limiting, anonymous rejection), publish flow (draft→published visibility across list/detail/RSS/sitemap), scheduling (use `freezegun` for future posts becoming visible), search (found by title/body, drafts excluded), slug-change redirects, image upload validation (size/EXIF/WebP), and ABV computation/recipe JSON round-trip.

## Assets

Logo assets in `specs/assets/` must be copied into `app/static/img/` during setup — use `logo-web.webp` (512px) for UI, not the 4.8MB `logo.png` original. Never generate a substitute logo; resize from `logo.png` if a needed size is missing.
