# Bifrost Brews — Backend Spec

## Data model

All tables have `id` (integer PK), `created_at`, `updated_at` (UTC). Articles and recipes share publishing fields but are **separate tables** — recipes carry structured brewing data.

### `posts` (articles)

| Column | Type | Notes |
|---|---|---|
| title | str, ≤200 | required |
| slug | str, unique | auto from title, editable |
| summary | str, ≤300 | shown on cards + meta description |
| body_md | text | markdown source |
| body_html | text | rendered+sanitized at save time |
| hero_image_id | FK images, nullable | card + OG image |
| status | enum: draft / scheduled / published | default draft |
| published_at | datetime, nullable | set on publish; future = scheduled |
| reading_minutes | int | computed at save (≈220 wpm) |
| view_count | int, default 0 | |

### `recipes`

All `posts` columns **plus**:

| Column | Type | Notes |
|---|---|---|
| style | str | e.g. traditional, melomel, cyser, metheglin, braggot, cider, other |
| batch_liters | float | batch size |
| og | float, nullable | original gravity, e.g. 1.110 |
| fg | float, nullable | final gravity, e.g. 1.010 |
| abv | float, nullable | if og+fg present, compute `(og-fg)*131.25`, allow manual override |
| difficulty | enum: beginner / intermediate / advanced | |
| ingredients_json | JSON | list of `{amount, unit, item, note?}` — rendered as ingredient cards |
| steps_json | JSON | list of `{day_offset, title, description}` — rendered as timeline (day 0 = brew day) |
| total_days | int | computed from max day_offset |

The recipe **body_md** is optional narrative ("why I brewed this") shown after the structured sections.

### `tags` / `post_tags` / `recipe_tags`

`tags(name unique, slug unique)`; join tables. Tags are shared across both content types. Created inline from the admin editor (comma input), never orphan-deleted automatically.

### `images`

`filename`, `path`, `thumb_path`, `width`, `height`, `alt_text`, `uploaded_at`. Deleting an image in admin requires confirmation and warns if referenced.

### `redirects`

`old_path unique → new_path` (slug changes). Checked in a 404 fallback handler → 301.

### `settings`

Key/value (text) store for site-editable content: `about_md` / `about_html` (About page), `site_tagline`. Editable via a simple `/admin/settings` form.

### `daily_views`

`(content_type, content_id, date, count)` unique on first three — powers the dashboard chart; `view_count` on the post is the running total.

### FTS

`search_index` FTS5 table: `(content_type, content_id, title, summary, body_text)`. Rebuilt for a row on every save/publish/unpublish. Query with `bm25` ranking, `snippet()` for result excerpts.

## Publishing state machine

- **draft** → visible only in admin; previewable via `/admin/posts/{id}/preview` (session-required)
- **scheduled** = status published-intent + `published_at` in the future
- **published** = `published_at <= now`

There is **no background worker**. "Is it live?" is a query predicate used by every public route:
`status != 'draft' AND published_at <= now()`. A scheduled post therefore appears automatically once its time passes. (Cheap, correct, phone-friendly. RSS/sitemap use the same predicate.)

## Routes

### Public (all GET, server-rendered)

| Route | Page |
|---|---|
| `/` | Home: hero, latest 3 recipes, latest 5 articles, tag cloud |
| `/articles` | Paginated article list (12/page) |
| `/articles/{slug}` | Article detail (+view count, related-by-tag posts) |
| `/recipes` | Recipe grid; filter query params: `?style=`, `?difficulty=`, `?tag=` |
| `/recipes/{slug}` | Recipe detail |
| `/tags/{slug}` | All content with tag, both types, newest first |
| `/search?q=` | FTS results; htmx endpoint `/search/partial?q=` returns results fragment for live search |
| `/about` | About page (markdown content from a `settings` key, editable in admin) |
| `/rss.xml`, `/sitemap.xml`, `/robots.txt` | Feeds |

404 fallback: check `redirects`; else render 404 page.

### Auth

- `GET/POST /admin/login` — username + password form. Argon2 verify. On success: signed session cookie (`HttpOnly`, `SameSite=Lax`, `Secure` when ENV=prod), 30-day expiry.
- `POST /admin/logout`
- Rate limit login: 5 failures / 15 min per IP (in-memory is fine), constant-time compare, generic error message.
- All `/admin/*` routes require session; redirect to login. CSRF token on every mutating form.

### Admin (session-required)

| Route | Function |
|---|---|
| `GET /admin` | Dashboard: total views, 30-day views chart (from `daily_views`), top 5 posts, drafts list, scheduled list |
| `GET /admin/posts`, `GET /admin/recipes` | Lists with status filter |
| `GET/POST /admin/posts/new`, `/admin/posts/{id}/edit` | Editor (same pattern for recipes) |
| `POST /admin/posts/{id}/publish` | Sets published_at (now, or the chosen future datetime → scheduled) |
| `POST /admin/posts/{id}/unpublish` / `delete` | Delete requires type-the-title confirmation |
| `GET /admin/posts/{id}/preview` | Renders public template for a draft |
| `GET /admin/images`, `POST /admin/images/upload` | Library grid + upload (drag-drop, htmx); returns markdown snippet `![alt](url)` to copy |
| `POST /admin/preview-markdown` | htmx: raw md in → rendered HTML fragment out (editor live preview, debounced 500ms) |
| `GET/POST /admin/settings` | Edit About page markdown + site tagline |

### Editor requirements

- Two-pane: markdown textarea + live preview (htmx). Fields: title, slug (auto, unlockable), summary, tags (comma input), hero image picker, status/schedule controls.
- Recipe editor additionally: style/difficulty selects, batch size, OG/FG (ABV auto-computes in-browser via Alpine, editable), ingredients repeater rows, steps repeater rows (day offset + title + description).
- Autosave draft every 30s via htmx when dirty. Warn on navigation with unsaved changes.

## Analytics

Middleware on public content detail routes: increment `view_count` and `daily_views` unless a valid admin session cookie is present or User-Agent matches a bot list. No cookies set for readers, no IP storage — privacy-clean.

## Validation & security summary

- Pydantic schemas on every form/endpoint; slugs `^[a-z0-9-]{1,80}$`
- Uploads: whitelist jpeg/png/webp, ≤10MB, verify magic bytes via Pillow open, re-encode (never serve originals), strip EXIF
- Rendered HTML sanitized with nh3 (allow standard tags + img + pre/code)
- Jinja2 autoescape on; never `|safe` except the sanitized `body_html`
- Security headers middleware: `X-Content-Type-Options`, `X-Frame-Options: DENY`, basic CSP (`default-src 'self'`)

## Tests (pytest, minimum)

1. Auth: wrong password fails, rate limit triggers, admin routes reject anonymous
2. Publish flow: draft invisible → publish → visible on list/detail/RSS/sitemap
3. Scheduling: future post hidden, becomes visible when clock passes (freezegun)
4. Search: seeded content found by title and body terms; drafts never in results
5. Slug change creates redirect; old URL 301s
6. Image upload: oversized rejected, EXIF stripped, WebP produced
7. ABV computation and recipe JSON round-trip
