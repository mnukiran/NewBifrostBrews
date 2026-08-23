# Project Overview

## What this is
A personal knowledge site about Gen AI courses, plus a small community forum
(initially scoped to sharing/discussing within the user's company — informal
"gossip"/discussion, not formal Q&A support).

Project name: **Bifrost Brews** — kept from the original repo/project name
even though the content has completely changed (recipes → Gen AI courses +
forum). Tagline options are in [[04-branding]].

## Repo history note
This repo previously held "BifrostBrews", a recipe-and-articles site
(FastAPI + Jinja2 + htmx + Alpine, SQLite). The user chose to repurpose this
repo rather than start a new one. The cleanup is **already done**: commit
`1183500` removed the entire old app from the tracked tree. The old code
(including its vendored htmx/Alpine/fonts) remains recoverable from git
history — e.g. `git show f57464e:app/static/js/htmx.min.js`.

We're deliberately reusing the same overall stack shape (FastAPI + Jinja2 +
htmx + Alpine + SQLite) because it already proved itself lightweight enough
to reasonably run under Termux on a phone, and there's no reason to
re-litigate that choice for a site with similar traffic/complexity
expectations.

## Scope phases

**Phase 1 (current): Plan + site shell**
- Planning docs (this folder).
- Minimal, modern, static-feeling site shell: home page, nav, empty/"coming
  soon" placeholders for Courses and Forum sections, about page.
- Design system established (see [[02-ui-design]]) so every later page just
  slots into it.
- No real course content yet, no forum backend yet.

**Phase 2: Courses knowledge section + admin editor**
- Data model + pages for browsing/reading about Gen AI courses.
- **Admin mode**: a login-gated editor where the admin (site owner) authors
  course content as rich HTML/CSS/JS — full creative control over how a
  course page looks, not just plain text fields. Content is stored in SQLite
  and rendered into the site shell. See [[01-architecture]] "Admin content
  authoring".
- **Embedded YouTube video**: course pages can embed YouTube videos that
  play in-page (responsive iframe embeds, lazy-loaded). The video streams
  from YouTube directly to the viewer's browser — zero load on the phone
  server. See [[02-ui-design]] "Video embed" for the component.
- Content itself (what courses, descriptions, notes) is explicitly OUT OF
  SCOPE for now per the user's instruction — only the scaffolding/structure
  + editor is built in this phase. `Assets/` (e.g. `Intro to agents.pdf`)
  is the eventual raw source material for this content.

**Phase 3: Forum**
- Simple accounts (username/password, session cookies — no OAuth needed for
  a small private community).
- Categories → threads → replies.
- Deliberately no heavy moderation tooling at first; add if actually needed.

**Phase 4: Deploy to phone**
- Get it running persistently under Termux on the **OnePlus 7T** running
  LineageOS (Snapdragon 855+, 8 GB RAM — comfortable headroom for this
  stack).
- See [[01-architecture]] "Hosting on Termux" for the concerns this raises.

## Experience bar
Even though the server is an old phone, the **visitor experience must feel
first-class**: fast loads (small pages, cached static assets), responsive
layout on mobile and desktop, light/dark theme, smooth in-page video
playback, and no janky half-styled pages. The design system in
[[02-ui-design]] exists to guarantee this; performance practices live in
[[01-architecture]] "Performance & UX practices".

## Explicit assumptions (flag if wrong)
- Single community/forum (not multi-tenant across multiple companies).
- Forum uses per-user accounts with **self-signup** (decided 2026-08-23):
  anyone can register at `/signup`. Setting the `BIFROST_INVITE_CODE` env
  var makes signup require that code — leave it unset on LAN, set it
  before exposing the site to the internet.
- There is exactly one **admin** (the site owner) — the admin account is
  fully trusted, which is why admin-authored raw HTML/CSS/JS can be rendered
  without sanitization (see [[01-architecture]] "Admin content authoring").
- Primary viewers are on laptop/phone browsers on the same network or over a
  tunnel (see hosting doc) — the phone is the **server**, not necessarily
  the only client.
- Viewers have internet access (YouTube embeds stream from YouTube's CDN,
  not from the phone) — the site itself still works on pure LAN, only the
  videos need internet.
- "Minimalistic but modern" = generous whitespace, restrained color, strong
  typography, few decorative elements — not "bare/unstyled".

## Open questions for the user
1. ~~Forum account creation~~ — decided: self-signup, with an optional
   invite-code gate via `BIFROST_INVITE_CODE` (see assumptions).
2. Do you want the phone reachable from outside your home network (needs a
   tunnel/relay — see [[01-architecture]]), or is LAN-only fine for now?
3. ~~Tagline~~ — decided: "Learn AI. Brew conversation." ([[04-branding]]).
