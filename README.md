# Bifrost Brews

A blog and recipe site about mead-making and other fermented/alcoholic beverages. "Nectar of the Gods."

Full product spec lives in `specs/`. Full engineering status, architecture notes, and a detailed list of workarounds/gotchas from the current build live in `CLAUDE.md` — **read that before making changes**, especially the "Known workarounds, dummy values, and gotchas" section.

## Current status (2026-07-06)

The full public-facing site is built and working: home, articles, recipes, tags, live search, about, and a custom 404, all backed by a real SQLite database and seeded with sample mead content. The admin panel (login, content editing, image uploads, scheduling) has not been built yet, so there is no way to add real content through the UI yet — only via `scripts/seed.py` or direct DB access.

See `CLAUDE.md` for the full done/pending breakdown.

## Prerequisites

- Python 3.12+
- Node.js (for the Tailwind CLI build step only — there is no JS framework/bundler beyond this)
- [`uv`](https://github.com/astral-sh/uv) for Python dependency management (`pip install uv` if you don't have it)

## Setup (first time)

```
uv sync
npm install
python -m uv run alembic upgrade head
python -m uv run python scripts/seed.py
```

This creates `data/bifrost.db` (gitignored) with the schema and sample content. `scripts/seed.py` is a no-op if the database already has content, so it's safe to re-run.

## Running locally

Two terminals:

```
# Terminal 1 -- Tailwind watch build
npm run css:watch

# Terminal 2 -- app server
python -m uv run uvicorn app.main:app --reload --port 8000
```

Then open http://localhost:8000.

If terminal 2 fails with "address already in use," something is already listening on port 8000 (Windows: `netstat -ano | findstr :8000` to find the PID, `taskkill /PID <pid> /F` to stop it).

## One-off commands

```
npm run css                                    # one-time production CSS build (minified)
python -m uv run alembic revision --autogenerate -m "message"   # new migration after model changes
python -m uv run alembic upgrade head          # apply migrations
python -m uv run pytest                        # run tests (none exist yet)
```

## Project layout

```
app/
  main.py, config.py, db.py, models.py, templating.py
  routers/public.py        # all current routes
  services/content.py      # queries, published-state filtering, FTS5 search, view counting
  services/markdown.py     # markdown -> sanitized HTML
  templates/                # Jinja2: base.html, partials/, public/
  static/                   # compiled CSS, vendored htmx/Alpine, self-hosted fonts, logo assets
alembic/                    # DB migrations
scripts/seed.py             # sample content seeder
styles/input.css            # Tailwind v4 source (theme tokens, fonts, custom prose/code CSS)
specs/                      # original product/architecture/backend/frontend specs
```

Nothing under `admin/` exists yet — see `CLAUDE.md` for what's next.
