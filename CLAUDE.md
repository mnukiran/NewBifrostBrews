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
- Admin: auth (login/logout, session cookies, CSRF, rate limiting), CRUD for posts/recipes, image upload pipeline (`app/services/images.py`), markdown live-preview endpoint, scheduling controls, `/admin/settings`, `scripts/set_password.py`
- `app/routers/feeds.py` — `/rss.xml`, `/sitemap.xml`, `/robots.txt` (base.html already links to `/rss.xml`, currently 404s)
- Analytics dashboard (30-day views chart, top posts) — `daily_views` table and `record_view()` already exist and are being written to, just no admin UI reads them yet
- Tests (`tests/`) per the spec's minimum list — the directory exists (with an empty `__init__.py` just so git tracks it) but zero tests are written
- A `Makefile`/`justfile` wrapping `make dev`/`make css`/`make test`/`make seed` (commands below work standalone for now)
- Security headers middleware, CSRF, rate limiting — none of this exists yet at all (see "Known workarounds" below)

## Known workarounds, dummy values, and gotchas

Read this before assuming anything is finished or secure. These are real shortcuts taken to get the public site working; each needs a deliberate decision (not just deletion) before the project goes further.

- **`.env` has throwaway values.** `SECRET_KEY=dev-secret-key-change-me` is a placeholder — regenerate it before session-signing (`itsdangerous`) is actually wired into admin auth, or every session cookie signed with it is forgeable by anyone who reads this repo. `ADMIN_PASSWORD_HASH` is blank because `scripts/set_password.py` doesn't exist yet — admin login literally cannot work until that script exists and is run. `.env` is gitignored (not in the GitHub repo); `.env.example` has empty placeholders as intended.
- **View counting has no exclusions yet.** `record_view()` in `app/services/content.py` increments `view_count`/`daily_views` on *every* visit to an article/recipe detail page, including your own testing and search-engine bots. The spec requires skipping admin sessions and known bots (`02-backend-spec.md` § Analytics) — that logic was deferred because admin sessions don't exist yet. Numbers you see in the DB right now are inflated by dev/QA traffic, not real.
- **`nh3.clean()` cannot allow `rel` on `<a>` tags.** Passing `"rel"` in the attribute allowlist for `a` in `app/services/markdown.py` crashes with a Rust panic (`ammonia` asserts you don't set `rel` manually because it manages that attribute internally). Don't re-add it — if you need to control `rel` behavior, use nh3's dedicated `link_rel` parameter instead.
- **No hero images exist anywhere.** Every seeded post/recipe has `hero_image_id = NULL`. All cards and detail pages render `app/templates/partials/_hero_placeholder.html` (a gradient block with a faded logo) instead of a real photo. This is intentional — no `app/services/images.py` exists yet to process uploads — but it means you have never actually seen the hero-image code path render a real image; test that carefully once uploads exist.
- **All seeded content is fake placeholder text**, clearly tagged `Sample Content` and ending in an italic "*This is placeholder sample content...*" disclaimer (see `scripts/seed.py`). Delete/replace it before anything resembling a real launch. Note one cosmetic quirk: the Day-0 timeline step in both sample recipes has its `title` field duplicate the "Brew Day" wording that's also auto-generated from `day_offset == 0` in `recipe_detail.html` — harmless, just slightly redundant in the two sample recipes specifically.
- **Redirect 404-fallback is wired but unreachable.** `app/main.py`'s 404 handler checks the `redirects` table before rendering the 404 page, exactly per spec — but nothing ever inserts a row into `redirects` yet (that happens on slug-change in the admin editor, which doesn't exist). Dead but harmless code path.
- **No FTS sync on edit — because there's no edit yet.** `rebuild_search_index_row()` is only ever called from `scripts/seed.py`. Once admin CRUD exists, every save/publish/unpublish route MUST call it (per `01-architecture.md` § Search) or the search index silently goes stale.
- **`data/` (the SQLite DB + uploads) is gitignored** and will NOT exist after a fresh clone. Anyone picking this up must run migrations + seed again (see Commands) before the site shows any content — it isn't "broken," it's just an empty DB.
- **Tooling substitutions from what the specs literally say:**
  - `uv` was installed via `pip install uv` (not a separate system package) — it's a normal Python package, works fine, just noting how it got there.
  - Tailwind CLI is the `tailwindcss`/`@tailwindcss/cli` **npm packages** (`package.json` devDependencies, v4.3.2), not the single downloadable standalone binary the architecture doc calls "the standalone CLI." Functionally identical (`npm run css` / `npm run css:watch`); a different agent shouldn't go looking for a `tailwindcss` executable outside `node_modules/.bin`.
  - htmx (`2.0.10`) and Alpine.js (`3.15.12`) were downloaded once from jsdelivr and committed as static files in `app/static/js/` — they are **not** npm-managed. Bumping versions means manually re-downloading and replacing those two files, not `npm update`.
  - Fonts (`app/static/fonts/*.woff2`) were downloaded once from Google Fonts (specific weights: Cinzel 600/700, Source Serif 4 400/400i/600, Inter 400/500/600, JetBrains Mono 400) and are committed as static files, referenced via `@font-face` in `styles/input.css`. No live Google Fonts dependency at runtime.
- **`datetime.utcnow()` deprecation warnings are expected noise.** Python 3.12 flags `datetime.utcnow()` (used consistently in `app/models.py`, `app/services/content.py`, `scripts/seed.py`) as deprecated in favor of timezone-aware datetimes. It still works correctly with SQLite's naive-datetime storage and matches the spec's "UTC ISO strings" requirement; left as-is rather than doing a project-wide timezone-aware refactor mid-build. If you tackle it, change it everywhere at once, not piecemeal.
- **A local (repo-only, not global) git identity was set**: `user.name = mnukiran`, `user.email = mnukiran@gmail.com`. A fresh clone on another machine, or a different agent's sandbox, may not have any git identity configured at all — if `git commit` fails with "Author identity unknown," that's expected and just needs the same one-time `git config` (see git history for the exact commands used).
- **A dev server may already be running.** During this build, `uvicorn` was started in the background on port 8000 for visual QA. It's tied to that terminal session and should not survive a closed session/reboot, but if a fresh `uvicorn app.main:app --reload --port 8000` fails with "address already in use," find and stop whatever's still holding port 8000 first (Windows: `netstat -ano | findstr :8000` then `taskkill /PID <pid> /F`).

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

Directory layout — what actually exists today (✓) vs. what the spec calls for but isn't built yet (planned):

```
app/main.py              # ✓ FastAPI app factory, static mount, 404/redirect handler
app/config.py             # ✓ pydantic-settings, reads .env
app/db.py                 # ✓ engine, session dependency, SQLite pragmas
app/models.py              # ✓ all SQLAlchemy models (posts, recipes, tags, images, redirects, settings, daily_views)
app/templating.py          # ✓ shared Jinja2Templates instance + dateformat filter (not in original spec tree,
                            #   added to avoid a circular import between main.py and routers/)
app/routers/
  public.py                # ✓ all public routes
  admin.py, auth.py        # planned — do not exist
  feeds.py                 # planned — do not exist (rss.xml/sitemap.xml/robots.txt all currently 404)
app/services/
  content.py                # ✓ query logic, published filter, FTS5 search, view counting
  markdown.py                # ✓ md -> sanitized HTML, reading-time calc
  images.py, analytics.py    # planned — do not exist
app/templates/
  base.html, partials/, public/   # ✓ all built
  admin/                          # planned — does not exist
alembic/                    # ✓ migrations (initial schema + FTS5 virtual table)
scripts/seed.py              # ✓ sample content seeder
scripts/set_password.py       # planned — does not exist (blocks admin auth)
styles/input.css              # ✓ Tailwind v4 source with @theme tokens + hand-written prose/pygments CSS
tests/                        # exists as an empty package (see gotchas above); zero tests written
```

See `specs/01-architecture.md` for the full originally-intended tree.

Key architectural decisions that shape how code should be written here:

- **Markdown is rendered at save time**, not per-request. `body_md` → sanitized `body_html` is cached in the DB and re-rendered only on edit. Never render markdown in a hot request path.
- **No background worker/scheduler.** "Is a post live?" is just the predicate `status != 'draft' AND published_at <= now()`, applied identically by every public route, RSS, and the sitemap. Scheduled posts become visible automatically once real time passes it — don't build a cron/worker for this.
- **Articles and recipes are separate tables** (`posts`, `recipes`) sharing publishing fields (status/published_at/slug/etc.), not a shared polymorphic table. Recipes add structured brewing data (`ingredients_json`, `steps_json`, OG/FG/ABV) plus an optional narrative `body_md`.
- **Search is SQLite FTS5** (`search_index` virtual table), kept in sync by explicit rebuild-on-save/publish/unpublish in the service layer — no DB triggers.
- **Images**: validate → strip EXIF → resize (max 1600px + 400px thumb) → re-encode to WebP at upload time; originals are never served. Stored at `data/uploads/YYYY/MM/{slug}-{shortid}.webp`.
- **Slug changes** after publish write an entry to a `redirects` table, checked in the 404 handler for a 301.
- **SQLite pragmas**: WAL mode, `busy_timeout=5000`, `foreign_keys=ON` — set on connect. One writer (admin) + many readers is the expected access pattern.
- **Analytics** *should* be middleware-based view counting (`view_count` + `daily_views`) on public detail routes, skipped for admin sessions and known bots, per spec. Currently implemented as a plain function call (`record_view()`) inside each detail route with **no exclusions at all** — see "Known workarounds" above. No cookies or IP storage for readers either way.
- Timestamps stored as UTC ISO strings; rendered in `SITE_TZ` from config.

Full data model, routes, and the publishing state machine are in `specs/02-backend-spec.md`. Full design system (colors, type, components, page layouts) is in `specs/03-frontend-ui-spec.md` — the palette and Cinzel/Source Serif 4/Inter/JetBrains Mono type roles are derived from the logo and should be implemented as Tailwind `@theme` tokens, not ad-hoc values.

## Performance budget (phone-aware — treat as hard requirements, not aspirations)

- Reader-facing JS < 50KB gzipped total; CSS < 30KB gzipped.
- No N+1 queries (eager-load tags); no per-request markdown rendering.
- Images always WebP with explicit width/height attributes (no layout shift).
- Lighthouse performance ≥ 90 and accessibility ≥ 95 on article/recipe pages.

## Security summary (from `specs/02-backend-spec.md`)

Target state per spec — **none of the auth/CSRF/rate-limiting/headers items below are implemented yet**, since there is no admin surface to protect and no forms accept write input yet. Only the sanitization/autoescape items are actually active today.

- Pydantic validation on every form/endpoint; slugs constrained to `^[a-z0-9-]{1,80}$`. *(not yet applicable — no write endpoints exist)*
- Uploads: whitelist jpeg/png/webp, ≤10MB, verify magic bytes via Pillow, always re-encode, strip EXIF. *(not built — no upload endpoint exists)*
- **✓ active today:** rendered HTML sanitized with `nh3` (see the `rel`-attribute gotcha above); Jinja2 autoescape on — never use `|safe` except on the already-sanitized `body_html`/`about_html`.
- Argon2 password hashing, signed session cookies (`itsdangerous`), CSRF token on mutating admin forms, login rate-limited (5 failures / 15 min / IP). *(not built — `argon2-cffi`/`itsdangerous` are installed as dependencies but unused so far)*
- Security headers middleware: `X-Content-Type-Options`, `X-Frame-Options: DENY`, basic CSP. *(not built)*

## Testing

Minimum pytest coverage per `specs/02-backend-spec.md` § Tests: auth (bad password, rate limiting, anonymous rejection), publish flow (draft→published visibility across list/detail/RSS/sitemap), scheduling (use `freezegun` for future posts becoming visible), search (found by title/body, drafts excluded), slug-change redirects, image upload validation (size/EXIF/WebP), and ABV computation/recipe JSON round-trip.

## Assets

Logo assets in `specs/assets/` must be copied into `app/static/img/` during setup — use `logo-web.webp` (512px) for UI, not the 4.8MB `logo.png` original. Never generate a substitute logo; resize from `logo.png` if a needed size is missing.
