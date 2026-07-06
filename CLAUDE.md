# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

The specs (`specs/00-overview.md` through `specs/03-frontend-ui-spec.md`) are written for an AI coding agent to implement from scratch — read all four before making further changes, since they cross-reference each other (e.g. the data model in `02-backend-spec.md` depends on directory layout in `01-architecture.md`).

The build order was deliberately reshuffled from the spec's default sequence: instead of DB models → public routes → admin → design system, this project did skeleton + Tailwind/fonts → DB models → **all public routes and templates with the full design system applied, wired to a real seeded DB** → (admin still pending). This was a user choice to see the real frontend early, not a spec change.

**Done:**
- Project skeleton (`pyproject.toml`, `app/config.py`, `app/db.py`, `app/main.py`), dependencies installed via `uv`
- Tailwind v4 CLI pipeline (`styles/input.css` → `app/static/css/site.css`) with the full theme token set, self-hosted fonts (Cinzel/Source Serif 4/Inter/JetBrains Mono as woff2), vendored htmx + Alpine, logo assets copied into `app/static/img/`
- SQLAlchemy models for all tables in `02-backend-spec.md` (`app/models.py`) + Alembic migrations, including the FTS5 `search_index` virtual table
- `scripts/seed.py` — 3 sample articles + 2 sample recipes, tagged "Sample Content"
- `app/services/content.py` (published-state filtering, pagination, tag queries, FTS5 search, view counting) and `app/services/markdown.py` (markdown-it-py → nh3-sanitized HTML, Pygments highlighting, reading-time calc)
- All public routes + templates (`app/routers/public.py`, `app/templates/`): home, article list/detail, recipe list/detail with style/difficulty filters, tag pages, live htmx search + full search page, about, custom 404 — visually verified in-browser at desktop and mobile widths

**Not yet built (next steps, in spec's intended order):**
- Admin: auth (login/logout, session cookies, CSRF, rate limiting), CRUD for posts/recipes, image upload pipeline (`app/services/images.py`), markdown live-preview endpoint, scheduling controls, `/admin/settings`
- `app/routers/feeds.py` — `/rss.xml`, `/sitemap.xml`, `/robots.txt` (base.html already links to `/rss.xml`, currently 404s)
- Analytics dashboard (30-day views chart, top posts) — `daily_views` table and `record_view()` already exist and are being written to, just no admin UI reads them yet
- Tests (`tests/`) per the spec's minimum list — none written yet
- A `Makefile`/`justfile` wrapping `make dev`/`make css`/`make test`/`make seed` (commands below work standalone for now)

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

## Commands

These are already set up and working (no `set_password.py` yet since admin auth isn't built):

```
uv sync                                                    # install Python deps
npm install                                                # install Tailwind CLI (devDependency)
python -m uv run alembic upgrade head                      # run migrations
python -m uv run python scripts/seed.py                    # seed sample content (skips if DB already has content)
npm run css:watch                                          # terminal 1: Tailwind watch build
python -m uv run uvicorn app.main:app --reload --port 8000 # terminal 2 -> http://localhost:8000
```

No `Makefile`/`justfile` exists yet (per the spec, one should wrap these as `make dev`/`make css`/`make test`/`make seed`). No `scripts/set_password.py` yet either — that's part of the pending admin-auth work. Tests run via `pytest` once written (see Testing below); none exist yet.

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
