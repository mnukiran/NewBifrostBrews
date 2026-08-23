# Task List

Status legend: `[x]` done · `[ ]` pending · `[~]` in progress

## Phase 0 — Planning
- [x] Decide to reuse this repo instead of starting a new one.
- [x] Decide tech stack (FastAPI + Jinja2 + htmx + Alpine + SQLite, plain CSS).
- [x] Write overview doc ([[00-overview]]).
- [x] Write architecture doc, incl. Termux hosting concerns ([[01-architecture]]).
- [x] Write UI design style guide ([[02-ui-design]]).
- [x] Write branding doc with tagline options ([[04-branding]]).
- [x] Remove old BifrostBrews app code (done in commit `1183500`; old code
      + vendored assets remain recoverable from git history).
- [x] Fold in hosting/UX requirements: OnePlus 7T target, admin HTML/CSS/JS
      content editor, in-page YouTube playback.
- [ ] Remaining open question in [[00-overview]]: LAN-only vs
      internet-reachable (decide before Phase 4; account creation and
      tagline are settled).

## Phase 1 — Site shell
- [x] New `pyproject.toml` from scratch (fastapi, uvicorn, jinja2 — no
      alembic/ORM per [[01-architecture]]).
- [x] `app/main.py` + `app/config.py` + `app/db.py` skeleton.
- [x] Base template (`base.html`) with nav, footer, design tokens as CSS
      custom properties from [[02-ui-design]].
- [x] Home page.
- [x] About page.
- [x] Empty/"coming soon" placeholder pages for Courses and Forum.
- [x] Light/dark theme via `prefers-color-scheme`.
- [x] Vendor htmx.min.js + Alpine.min.js + fonts (recover from git history
      — e.g. `git show f57464e:app/static/...` — or re-fetch fresh).
- [x] GZip middleware + static-asset cache headers ([[01-architecture]]
      "Performance & UX practices").
- [x] Smoke-test locally on laptop (`uvicorn app.main:app --reload`).

## Phase 2 — Courses section + admin editor (no real content yet)
- [x] `courses` table/schema (content stored in SQLite: `body_html`,
      `custom_css`, `custom_js`, `published` — see [[01-architecture]]
      "Admin content authoring").
- [x] `users` table + scrypt password hashing + session cookie auth for the
      single admin account (Phase 3 reuses this for forum users).
- [x] Admin router + login page.
- [x] Admin course editor: HTML/CSS/JS textareas, htmx live preview,
      draft/publish toggle ([[02-ui-design]] "Admin editor").
- [x] Course list page (grid of cards, using [[02-ui-design]] card
      component; published courses only).
- [x] Course detail page rendering admin content (unescaped `body_html` in
      a `.course-content` container + scoped custom CSS/JS).
- [x] YouTube embed support: responsive 16:9 facade component (thumbnail +
      play button → swaps to `youtube-nocookie.com` iframe, plays in-page)
      and `{{yt:VIDEO_ID}}` shortcode expansion in the content service.
- [x] SQLite `PRAGMA journal_mode=WAL` + `synchronous=NORMAL` in `db.py`
      (done early — the Phase 1 `db.py` skeleton already sets them).

## Phase 3 — Forum
- [x] Decide account-creation mechanism: self-signup at `/signup`, optional
      invite-code gate via `BIFROST_INVITE_CODE` env var.
- [x] Extend Phase 2 auth to regular (non-admin) forum users: shared
      `/login` + `/signup` + `/logout`, current-user middleware, logged-in
      state in the nav, forum page gated to members.
- [x] `categories`, `threads`, `posts` tables (seeded default categories).
- [x] Category list → thread list → thread detail pages.
- [x] New thread / reply forms (htmx partial submit, no full reload).
- [x] Basic abuse safeguard: 15s per-user post cooldown, admin can
      hide/unhide posts and delete threads — not full moderation tooling.

## Phase 4 — Deploy to phone (Termux on the OnePlus 7T)
- [ ] Install Termux + required packages (python, sqlite, termux-services,
      termux-api) on the OnePlus 7T (LineageOS).
- [ ] `scripts/serve.sh` — acquire `termux-wake-lock`, run uvicorn.
- [ ] Wire up as a `termux-services` supervised service.
- [ ] Install `Termux:Boot` companion app, add boot script for auto-start.
- [ ] Decide + implement reachability (Tailscale, tunnel, or LAN-only).
- [ ] DB backup job (copy SQLite file off-device periodically).
- [ ] End-to-end test: reboot the phone, confirm site comes back up on its
      own.

## Explicitly deferred / not doing yet
- Real course content/data entry.
- OAuth or third-party login for the forum.
- Any moderation dashboard beyond a basic delete/hide.
- Multi-tenant support for more than one company/community.
- Containerization.
