"""Course content rendering: expands {{yt:VIDEO_ID}} shortcodes into the
responsive click-to-load YouTube facade (see Plan/01-architecture.md,
"YouTube embeds"). The real iframe is injected on click by
static/js/yt-embed.js — un-clicked pages stay light."""
import re

YT_RE = re.compile(r"\{\{\s*yt:([A-Za-z0-9_-]{5,20})\s*\}\}")

YT_FACADE = (
    '<div class="yt-embed">'
    '<button type="button" class="yt-embed__facade" data-yt-id="{vid}" '
    'aria-label="Play video">'
    '<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy">'
    '<span class="yt-embed__play" aria-hidden="true"></span>'
    "</button></div>"
)


def render_body(body_html: str) -> str:
    return YT_RE.sub(lambda m: YT_FACADE.format(vid=m.group(1)), body_html)
