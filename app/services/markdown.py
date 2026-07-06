import re

import nh3
from markdown_it import MarkdownIt
from pygments import highlight as pygments_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

WORDS_PER_MINUTE = 220

_ALLOWED_TAGS = {
    "p", "br", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "em", "b", "i", "u", "s", "del",
    "ul", "ol", "li",
    "a", "img",
    "blockquote",
    "pre", "code", "span",
    "table", "thead", "tbody", "tr", "th", "td",
}

_ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "id"},
    "img": {"src", "alt", "title", "width", "height"},
    "code": {"class"},
    "pre": {"class"},
    "span": {"class"},
    "*": {"id"},
}


def _highlight(code: str, lang: str, _attrs: str) -> str:
    formatter = HtmlFormatter(nowrap=True)
    try:
        lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
    except ClassNotFound:
        lexer = get_lexer_by_name("text")
    highlighted = pygments_highlight(code, lexer, formatter)
    return f'<pre class="highlight"><code>{highlighted}</code></pre>'


_md = MarkdownIt("commonmark", {"highlight": _highlight}).enable(["table"])


def render_markdown(body_md: str) -> str:
    raw_html = _md.render(body_md)
    return nh3.clean(raw_html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES)


def reading_minutes(body_md: str) -> int:
    word_count = len(re.findall(r"\S+", body_md))
    return max(1, round(word_count / WORDS_PER_MINUTE))
