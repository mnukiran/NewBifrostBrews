import sqlite3
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.db import get_db
from app.templating import templates

router = APIRouter(prefix="/forum")

# Minimum seconds between posts by one user — a light brake on
# accidental double-posts and spam, not real moderation tooling.
POST_COOLDOWN_SECONDS = 15
MAX_POST_LENGTH = 10_000
MAX_TITLE_LENGTH = 200


def require_member(request: Request) -> sqlite3.Row:
    user = request.state.user
    if user is not None:
        return user
    raise HTTPException(
        status_code=303,
        headers={"Location": f"/login?next={quote(request.url.path)}"},
    )


def require_admin(request: Request) -> sqlite3.Row:
    user = request.state.user
    if user is not None and user["is_admin"]:
        return user
    raise HTTPException(status_code=403, detail="Admins only")


def cooldown_active(conn: sqlite3.Connection, user_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM posts WHERE user_id = ? "
        "AND created_at > datetime('now', ?) LIMIT 1",
        (user_id, f"-{POST_COOLDOWN_SECONDS} seconds"),
    ).fetchone()
    return row is not None


@router.get("")
def index(request: Request):
    if request.state.user is None:
        return templates.TemplateResponse(
            request, "forum/locked.html", {"active": "forum"}
        )
    with get_db() as conn:
        categories = conn.execute(
            """SELECT c.*, COUNT(t.id) AS thread_count
               FROM categories c LEFT JOIN threads t ON t.category_id = c.id
               GROUP BY c.id ORDER BY c.sort"""
        ).fetchall()
    return templates.TemplateResponse(
        request, "forum/index.html", {"active": "forum", "categories": categories}
    )


@router.get("/c/{slug}")
def category(request: Request, slug: str, user=Depends(require_member)):
    with get_db() as conn:
        cat = conn.execute(
            "SELECT * FROM categories WHERE slug = ?", (slug,)
        ).fetchone()
        if cat is None:
            raise HTTPException(status_code=404)
        threads = conn.execute(
            """SELECT t.id, t.title, t.updated_at,
                      COALESCE(u.username, '[deleted]') AS username,
                      COUNT(p.id) - 1 AS reply_count
               FROM threads t
               LEFT JOIN users u ON u.id = t.user_id
               LEFT JOIN posts p ON p.thread_id = t.id AND p.hidden = 0
               WHERE t.category_id = ?
               GROUP BY t.id ORDER BY t.updated_at DESC""",
            (cat["id"],),
        ).fetchall()
    return templates.TemplateResponse(
        request,
        "forum/category.html",
        {"active": "forum", "category": cat, "threads": threads, "error": None},
    )


@router.post("/c/{slug}/threads")
def create_thread(
    request: Request,
    slug: str,
    user=Depends(require_member),
    title: str = Form(...),
    body: str = Form(...),
):
    title, body = title.strip(), body.strip()
    with get_db() as conn:
        cat = conn.execute(
            "SELECT * FROM categories WHERE slug = ?", (slug,)
        ).fetchone()
        if cat is None:
            raise HTTPException(status_code=404)
        error = None
        if not title or not body:
            error = "Title and message are both required."
        elif len(title) > MAX_TITLE_LENGTH or len(body) > MAX_POST_LENGTH:
            error = "That's a bit long — trim the title or message."
        elif cooldown_active(conn, user["id"]):
            error = f"Slow down — wait {POST_COOLDOWN_SECONDS}s between posts."
        if error:
            threads = conn.execute(
                """SELECT t.id, t.title, t.updated_at,
                      COALESCE(u.username, '[deleted]') AS username,
                          COUNT(p.id) - 1 AS reply_count
                   FROM threads t LEFT JOIN users u ON u.id = t.user_id
                   LEFT JOIN posts p ON p.thread_id = t.id AND p.hidden = 0
                   WHERE t.category_id = ? GROUP BY t.id
                   ORDER BY t.updated_at DESC""",
                (cat["id"],),
            ).fetchall()
            return templates.TemplateResponse(
                request,
                "forum/category.html",
                {"active": "forum", "category": cat, "threads": threads,
                 "error": error},
                status_code=400,
            )
        cur = conn.execute(
            "INSERT INTO threads (category_id, user_id, title) VALUES (?, ?, ?)",
            (cat["id"], user["id"], title),
        )
        conn.execute(
            "INSERT INTO posts (thread_id, user_id, body) VALUES (?, ?, ?)",
            (cur.lastrowid, user["id"], body),
        )
    return RedirectResponse(f"/forum/t/{cur.lastrowid}", status_code=303)


def load_thread(conn: sqlite3.Connection, thread_id: int):
    thread = conn.execute(
        """SELECT t.*, c.name AS category_name, c.slug AS category_slug
           FROM threads t JOIN categories c ON c.id = t.category_id
           WHERE t.id = ?""",
        (thread_id,),
    ).fetchone()
    if thread is None:
        raise HTTPException(status_code=404)
    posts = conn.execute(
        """SELECT p.*, COALESCE(u.username, '[deleted]') AS username FROM posts p
           LEFT JOIN users u ON u.id = p.user_id
           WHERE p.thread_id = ? ORDER BY p.created_at, p.id""",
        (thread_id,),
    ).fetchall()
    return thread, posts


@router.get("/t/{thread_id}")
def thread_detail(request: Request, thread_id: int, user=Depends(require_member)):
    with get_db() as conn:
        thread, posts = load_thread(conn, thread_id)
    return templates.TemplateResponse(
        request,
        "forum/thread.html",
        {"active": "forum", "thread": thread, "posts": posts, "error": None},
    )


@router.post("/t/{thread_id}/reply")
def reply(
    request: Request,
    thread_id: int,
    user=Depends(require_member),
    body: str = Form(...),
):
    body = body.strip()
    is_htmx = request.headers.get("HX-Request") == "true"
    with get_db() as conn:
        thread, _ = load_thread(conn, thread_id)
        error = None
        if not body:
            error = "Write something first."
        elif len(body) > MAX_POST_LENGTH:
            error = "That's a bit long — trim the message."
        elif cooldown_active(conn, user["id"]):
            error = f"Slow down — wait {POST_COOLDOWN_SECONDS}s between posts."
        if error:
            if is_htmx:
                # 200 + retarget headers: htmx doesn't swap 4xx bodies, and
                # X-Form-Error tells the form's reset handler to stand down.
                response = templates.TemplateResponse(
                    request, "forum/_reply_error.html", {"error": error}
                )
                response.headers["HX-Retarget"] = "#reply-slot"
                response.headers["HX-Reswap"] = "innerHTML"
                response.headers["X-Form-Error"] = "1"
                return response
            _, posts = load_thread(conn, thread_id)
            return templates.TemplateResponse(
                request,
                "forum/thread.html",
                {"active": "forum", "thread": thread, "posts": posts,
                 "error": error},
                status_code=400,
            )
        cur = conn.execute(
            "INSERT INTO posts (thread_id, user_id, body) VALUES (?, ?, ?)",
            (thread_id, user["id"], body),
        )
        conn.execute(
            "UPDATE threads SET updated_at = datetime('now') WHERE id = ?",
            (thread_id,),
        )
        post = conn.execute(
            """SELECT p.*, COALESCE(u.username, '[deleted]') AS username FROM posts p
               LEFT JOIN users u ON u.id = p.user_id WHERE p.id = ?""",
            (cur.lastrowid,),
        ).fetchone()
    if is_htmx:
        return templates.TemplateResponse(
            request, "forum/_post.html", {"post": post}
        )
    return RedirectResponse(f"/forum/t/{thread_id}", status_code=303)


@router.post("/posts/{post_id}/toggle-hidden")
def toggle_hidden(request: Request, post_id: int, user=Depends(require_admin)):
    with get_db() as conn:
        post = conn.execute(
            "SELECT thread_id FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
        if post is None:
            raise HTTPException(status_code=404)
        conn.execute(
            "UPDATE posts SET hidden = 1 - hidden WHERE id = ?", (post_id,)
        )
    return RedirectResponse(f"/forum/t/{post['thread_id']}", status_code=303)


@router.post("/t/{thread_id}/delete")
def delete_thread(request: Request, thread_id: int, user=Depends(require_admin)):
    with get_db() as conn:
        thread = conn.execute(
            """SELECT c.slug FROM threads t
               JOIN categories c ON c.id = t.category_id WHERE t.id = ?""",
            (thread_id,),
        ).fetchone()
        if thread is None:
            raise HTTPException(status_code=404)
        conn.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
    return RedirectResponse(f"/forum/c/{thread['slug']}", status_code=303)
