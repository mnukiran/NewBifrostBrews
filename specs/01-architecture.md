# Bifrost Brews — Architecture

## Stack

| Layer | Choice | Why |
|---|---|---|
| Web framework | FastAPI (Python 3.12+) | Async, fast, typed, great docs |
| Server | uvicorn | Standard ASGI server |
| Templates | Jinja2 (via `fastapi.templating`) | Server-rendered HTML |
| ORM | SQLAlchemy 2.x + SQLite | Single-file DB, zero server overhead |
| Migrations | Alembic | Schema evolution without data loss |
| CSS | Tailwind CSS v4 via standalone CLI | Compiled, purged, tiny output |
| Interactivity | htmx 2.x + Alpine.js 3.x (vendored local copies, not CDN) | Partial page updates, dropdowns/toggles |
| Markdown | `markdown-it-py` + `pygments` (code highlighting) | Render article bodies server-side |
| Sanitization | `nh3` | Sanitize rendered HTML (admin-only input, but defense in depth) |
| Images | `Pillow` | Resize/convert uploads to WebP |
| Auth/session | `itsdangerous` signed cookies + `argon2-cffi` password hash | No heavyweight auth framework |
| Config | `pydantic-settings` reading `.env` | Typed settings |

Dependency management: `uv` (or pip + `requirements.txt` if uv unavailable). Pin all versions.

## Directory layout

```
bifrostbrews/
├── app/
│   ├── main.py              # FastAPI app factory, middleware, startup
│   ├── config.py            # Settings (pydantic-settings)
│   ├── db.py                # Engine, session dependency
│   ├── models.py            # SQLAlchemy models
│   ├── routers/
│   │   ├── public.py        # Home, articles, recipes, tags, search, about
│   │   ├── admin.py         # Admin panel routes
│   │   ├── auth.py          # Login/logout
│   │   └── feeds.py         # sitemap.xml, rss.xml, robots.txt
│   ├── services/
│   │   ├── content.py       # Query logic: published filter, search, related posts
│   │   ├── markdown.py      # md → sanitized HTML, reading-time calc
│   │   ├── images.py        # Upload processing, resize, WebP
│   │   └── analytics.py     # View counting
│   ├── templates/
│   │   ├── base.html        # Layout: head, nav, footer, meta/OG blocks
│   │   ├── partials/        # _article_card, _recipe_card, _tag_pill, _pagination, _search_results
│   │   ├── public/          # home, article_list, article_detail, recipe_list, recipe_detail, tag, search, about, 404
│   │   └── admin/           # login, dashboard, post_list, post_edit, images, settings
│   └── static/
│       ├── css/site.css     # Tailwind build output (generated, gitignored)
│       ├── js/htmx.min.js, js/alpine.min.js
│       └── img/logo.png, img/favicon…
├── styles/input.css         # Tailwind source (@theme tokens per 03-frontend-ui-spec)
├── data/                    # gitignored
│   ├── bifrost.db           # SQLite
│   └── uploads/YYYY/MM/     # processed images
├── alembic/                 # migrations
├── scripts/seed.py          # sample content seeder
├── tests/                   # pytest: auth, publish flow, scheduling, search
├── .env.example
├── pyproject.toml
└── README.md                # run instructions
```

## Key decisions

**Rendering model.** Every public page is a full server-rendered HTML document. htmx is used only for enhancements: search-as-you-type results, admin editor live preview, pagination without full reload. Site must be fully functional with JS disabled (search falls back to form GET submit).

**Markdown pipeline.** Article/recipe bodies are stored as markdown, rendered to HTML at **save time** and cached in a `body_html` column (re-rendered on every edit). Rendering per-request is wasted CPU — remember the phone target.

**SQLite settings.** Enable WAL mode and `busy_timeout` on connect (`PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON`). One writer (admin) + many readers is SQLite's ideal case.

**Search.** SQLite FTS5 virtual table over title, summary, and body text of published content. Keep it in sync by rebuilding the row in the service layer on every save/publish/unpublish (no triggers — simpler, fine at blog scale). No external search engine.

**Images.** On upload: validate type, strip EXIF, resize to max 1600px wide, encode WebP (quality 82) plus a 400px thumbnail. Store under `data/uploads/YYYY/MM/{slug}-{shortid}.webp`. Serve via FastAPI StaticFiles with long cache headers.

**Slugs.** Auto-generated from title (lowercase, hyphenated, ASCII), editable in admin, unique per content type. Changing a slug after publishing keeps the old slug in a `redirects` table → 301.

**Time.** Store all timestamps as UTC ISO strings; render in site timezone from config (`SITE_TZ`, default `Asia/Kolkata` — confirm with owner).

**Errors.** Custom 404 page (on-brand: "You've sailed off the rainbow"). 500 handler logs traceback to file, shows generic page.

## Config (.env)

```
SECRET_KEY=            # session signing (generate on setup)
ADMIN_USERNAME=
ADMIN_PASSWORD_HASH=   # argon2; provide scripts/set_password.py to generate
DATABASE_URL=sqlite:///data/bifrost.db
SITE_URL=https://bifrostbrews.co   # used for canonical/OG/sitemap URLs
SITE_TZ=Asia/Kolkata
ENV=dev                            # dev|prod: toggles reload, cookie Secure flag
```

## SEO

- `base.html` exposes blocks for title, meta description, canonical, OpenGraph + Twitter card (article image or logo fallback)
- JSON-LD: `Article` for articles, `Recipe` for recipes (Google recipe rich results)
- `/sitemap.xml` (published content only), `/rss.xml` (latest 20), `/robots.txt` (disallow `/admin`)

## Local dev

```
uv sync                          # install deps
python scripts/set_password.py  # create .env admin credentials
alembic upgrade head
python scripts/seed.py           # optional sample content
tailwindcss -i styles/input.css -o app/static/css/site.css --watch   # terminal 1
uvicorn app.main:app --reload    # terminal 2 → http://localhost:8000
```

README must document exactly this. Provide a `Makefile` (or `justfile`) with `make dev`, `make css`, `make test`, `make seed`.

## Performance budget (phone-aware)

- No per-request markdown rendering, no N+1 queries (eager-load tags)
- Reader-facing JS < 50KB gzipped total; CSS < 30KB gzipped
- Images always WebP with explicit width/height (no layout shift)
- Target: article page TTFB < 50ms locally, Lighthouse perf ≥ 90
