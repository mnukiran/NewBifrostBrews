# Architecture

## Tech stack
- **Backend**: Python, FastAPI. Chosen over Flask for async support (nicer
  under low-resource Termux — non-blocking I/O instead of a thread per
  request) and because it's the same shape as the previous app in this repo,
  so patterns (routers/services split) carry over.
- **Templates**: Jinja2, server-rendered HTML. No client-side framework/SPA
  — keeps the JS footprint tiny, which matters both for "minimalistic" feel
  and for not needing a Node build step in Termux at runtime.
- **Interactivity**: htmx (partial page updates — e.g. posting a forum reply
  without a full reload) + Alpine.js (small bits of client-side state, e.g.
  a mobile nav toggle). Vendored `.min.js` files — no CDN dependency, works
  offline/on-LAN. (The old project's copies were deleted with the cleanup
  commit; recover them from git history or re-fetch fresh versions.)
- **Styling**: plain CSS with custom properties (design tokens) — see
  [[02-ui-design]]. No Tailwind build step, to avoid needing Node on the
  phone and to keep the CSS bundle intentionally small and hand-curated,
  which suits "minimalistic."
- **DB**: SQLite via a thin data-access layer (no ORM required at this
  scale — the old project's `app/db.py` pattern of raw SQL + a couple of
  helper functions is enough, and it's one less dependency to install under
  Termux's pip). Migrations via a plain versioned SQL scripts folder rather
  than Alembic, unless the schema turns out to need real migration tooling.
- **Auth**: session cookie + password hash. Prefer stdlib
  `hashlib.scrypt` (no third-party dependency, no compiled wheel to worry
  about under Termux) over bcrypt. No third-party OAuth — unnecessary
  complexity for a small private forum. Auth arrives in **Phase 2** for the
  single admin account (the content editor needs it), and Phase 3 extends
  the same tables/session machinery to regular forum users.

## Admin content authoring (Phase 2)
The admin edits course content through a login-gated web UI, authoring
**raw HTML + CSS + JS** per course page for full visual control:

- **Storage**: content lives in SQLite — `courses.body_html`, plus optional
  `courses.custom_css` and `courses.custom_js` columns. Editing happens at
  runtime through the browser, so file-based content would fight the admin
  UI; the DB is the single source of truth (and rides along in the existing
  backup job).
- **Rendering**: course pages render inside the normal site shell
  (`base.html` nav/footer/theme). `body_html` is injected unescaped
  (`| safe` in Jinja2); `custom_css` goes into a scoped `<style>` block and
  `custom_js` into a `<script>` at the end of the page. Best practice:
  wrap admin content in a `.course-content` container and encourage scoping
  custom CSS under it, so a course's styles can't break the site chrome.
- **Trust model**: this is deliberately *unsanitized* HTML/JS. That is safe
  **only** because exactly one fully-trusted person (the site owner) can
  write it. Two hard rules follow: (1) admin credentials are never shared;
  (2) forum/user input is NEVER rendered unescaped — Jinja2 autoescape
  stays on everywhere, and only the course-body fields opt out.
- **Editor UX**: v1 is a large `<textarea>` (or three: HTML/CSS/JS) with a
  live preview pane (htmx fetches a rendered preview). No heavyweight
  WYSIWYG dependency — the admin writes HTML by choice. Autosave-to-draft
  and an explicit Publish flag (`courses.published`) so half-finished pages
  never show publicly.

## YouTube embeds (in-page playback)
Course pages embed YouTube videos that play in place. Best practices:

- **Embed markup**: standard iframe embed using the privacy-enhanced
  domain — `https://www.youtube-nocookie.com/embed/<VIDEO_ID>` — with
  `loading="lazy"`, `allowfullscreen`, and
  `allow="accelerometer; autoplay; clipboard-write; encrypted-media;
  gyroscope; picture-in-picture"`.
- **Responsive sizing**: wrap in a container with `aspect-ratio: 16 / 9;
  width: 100%` so it scales on phones and desktops (see [[02-ui-design]]
  "Video embed" component).
- **Keep pages light (facade pattern)**: a raw YouTube iframe pulls ~1 MB of
  player JS per embed even if never played. For pages with multiple videos,
  render a thumbnail facade (`https://i.ytimg.com/vi/<ID>/hqdefault.jpg` +
  play button) and swap in the real iframe on click (a few lines of
  vanilla/Alpine JS — no library needed). Single-video pages can use a
  plain lazy iframe.
- **Server impact: none.** Video streams YouTube → viewer directly; the
  phone only serves the small HTML page. This is exactly the right media
  strategy for a phone-hosted site — never proxy or self-host video.
- **Authoring convenience**: the admin can paste a full iframe into
  `body_html`, but also support a shortcode like `{{yt:VIDEO_ID}}` that the
  content service expands into the responsive facade markup — less
  boilerplate, consistent styling.
- **CSP note**: if a Content-Security-Policy header is added later, it must
  allow `frame-src https://www.youtube-nocookie.com` and
  `img-src https://i.ytimg.com`, and (because of admin custom JS/CSS)
  `'unsafe-inline'` for style/script — a strict CSP is largely off the
  table by design here; the trust model above is the actual defense.

## Performance & UX practices (the "good experience" checklist)
- **Cache static assets aggressively**: far-future `Cache-Control` +
  content-hashed filenames (or `?v=` query) for CSS/JS/fonts — repeat
  visits then only fetch the small HTML.
- **GZip**: enable Starlette's `GZipMiddleware` — HTML/CSS compress ~70%,
  which matters on a phone's uplink.
- **Small pages**: budget roughly < 100 KB transferred for a typical page
  (excluding YouTube's own player once a video is clicked).
- **SQLite tuning**: `PRAGMA journal_mode=WAL` (readers don't block the
  writer — matters once the forum gets concurrent traffic) and
  `PRAGMA synchronous=NORMAL`.
- **No blocking work in request handlers**: FastAPI async where I/O-bound;
  SQLite calls are fast enough at this scale to stay sync in threadpool
  (`def` route handlers), which is simpler and fine.
- **Perceived speed**: htmx partial updates for forum posting, `<link
  rel=preload>` for the one font file actually used above the fold,
  `font-display: swap` so text never blocks on fonts.

## Directory structure (target)
```
app/
  main.py                 # FastAPI app, mounts routers
  config.py                # settings (env vars, paths)
  db.py                    # sqlite connection + query helpers
  models.py                 # dataclasses / typed rows
  routers/
    public.py              # home, about, courses (read-only pages)
    admin.py                 # Phase 2: login-gated content editor
    forum.py                 # Phase 3
    auth.py                   # Phase 2 (admin login), extended Phase 3
  services/
    content.py               # course content loading, {{yt:ID}} expansion
  static/
    css/                     # hand-written CSS, design tokens
    js/                       # vendored htmx.min.js, alpine.min.js
    fonts/, img/
  templates/
    base.html
    public/
    admin/                    # Phase 2
    forum/                    # Phase 3
db/
  schema.sql                  # versioned plain-SQL migrations
scripts/
  serve.sh                    # Phase 4: wakelock + uvicorn (see below)
Plan/                          # this folder
Assets/                        # raw source material (course PDFs etc.)
pyproject.toml
```

## Hosting on Termux (OnePlus 7T, LineageOS)
Target device: **OnePlus 7T** — Snapdragon 855+, 8 GB RAM. That's genuinely
plenty for uvicorn + SQLite + a small forum; the constraints below are about
Android's process management and packaging, not raw horsepower. This is the
part that differs most from a normal deploy and should shape decisions now
rather than be an afterthought later:

- **Process persistence**: Android will kill background processes
  aggressively. Termux needs `termux-wake-lock` held while the server runs,
  and ideally `Termux:Boot` (a companion app) to auto-start the server after
  a phone reboot. Plan for a small shell script (`scripts/serve.sh`) that
  acquires the wakelock and starts uvicorn.
- **Process manager**: no systemd in Termux. Use `termux-services` (via
  `pkg install termux-services`) for a supervised, restart-on-crash service,
  rather than a bare `nohup`.
- **Server**: `uvicorn` running the FastAPI app directly is fine at this
  scale — no need for gunicorn/multiple workers on a phone.
- **Reachability**: decide LAN-only vs internet-reachable (open question in
  [[00-overview]]). Options if internet access is wanted, roughly in order
  of simplicity: Tailscale (private mesh, easiest, no port-forwarding) >
  Cloudflare Tunnel (public URL, free, a bit more setup) > manual port
  forward on the home router (exposes the phone directly — avoid unless
  you're comfortable hardening it). This decision doesn't block Phases 1–3.
- **Storage**: SQLite file lives on the phone's internal storage under
  Termux's home; back it up periodically (e.g. a cron-style `termux-job-
  scheduler` task copying the DB file to Drive/synced folder) since a single
  phone is a single point of failure for the forum's data.
- **Resource ceiling**: keep dependencies minimal — every extra pip package
  is another thing that may not have a prebuilt wheel for Termux's
  architecture and needs compiling on-device. Prefer stdlib or pure-Python
  packages where reasonable.

## Data model (sketch, to firm up in Phase 2/3)
- `courses` (Phase 2): id, slug, title, provider, url, tags, `body_html`,
  `custom_css`, `custom_js`, `published`, created/updated timestamps.
  Content lives **in this table** (decided — the admin edits it through the
  web UI, so the DB is the source of truth; no separate content files).
- `users` (Phase 2 for the single admin, extended Phase 3): id, username,
  password hash (scrypt), `is_admin`, plus a `sessions` table (or signed
  cookie) for login state.
- `threads`, `posts`, `categories` (Phase 3): standard forum shape, nothing
  exotic.

## Non-goals for now
- No SPA/client-side routing.
- No containerization (Docker is unnecessarily heavy for a Termux target).
- No multi-tenant support.
