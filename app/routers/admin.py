import re
import secrets
import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db import get_db
from app.security import hash_password
from app.services.content import render_body
from app.templating import templates

router = APIRouter(prefix="/admin")


def require_admin(request: Request) -> sqlite3.Row:
    user = request.state.user
    if user is not None and user["is_admin"]:
        return user
    raise HTTPException(
        status_code=303, headers={"Location": "/login?next=/admin/courses"}
    )


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "course"


def unique_slug(conn: sqlite3.Connection, base: str, exclude_id: int | None = None) -> str:
    slug, n = base, 2
    while True:
        row = conn.execute(
            "SELECT id FROM courses WHERE slug = ?", (slug,)
        ).fetchone()
        if row is None or row["id"] == exclude_id:
            return slug
        slug = f"{base}-{n}"
        n += 1


@router.get("")
def admin_root(user=Depends(require_admin)):
    return RedirectResponse("/admin/courses", status_code=303)


@router.get("/courses")
def course_list(request: Request, user=Depends(require_admin)):
    with get_db() as conn:
        courses = conn.execute(
            "SELECT * FROM courses ORDER BY updated_at DESC"
        ).fetchall()
    return templates.TemplateResponse(
        request, "admin/courses.html", {"courses": courses, "user": user}
    )


@router.get("/courses/new")
def new_course_form(request: Request, user=Depends(require_admin)):
    return templates.TemplateResponse(
        request, "admin/edit.html", {"course": None, "user": user}
    )


@router.get("/courses/{course_id}/edit")
def edit_course_form(request: Request, course_id: int, user=Depends(require_admin)):
    with get_db() as conn:
        course = conn.execute(
            "SELECT * FROM courses WHERE id = ?", (course_id,)
        ).fetchone()
    if course is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "admin/edit.html", {"course": course, "user": user}
    )


@router.post("/courses/save")
def save_course(
    user=Depends(require_admin),
    course_id: int | None = Form(None),
    title: str = Form(...),
    slug: str = Form(""),
    provider: str = Form(""),
    url: str = Form(""),
    tags: str = Form(""),
    summary: str = Form(""),
    body_html: str = Form(""),
    custom_css: str = Form(""),
    custom_js: str = Form(""),
    published: str = Form(""),
):
    is_published = 1 if published else 0
    base_slug = slugify(slug or title)
    with get_db() as conn:
        final_slug = unique_slug(conn, base_slug, exclude_id=course_id)
        if course_id is None:
            cur = conn.execute(
                """INSERT INTO courses
                   (slug, title, provider, url, tags, summary, body_html,
                    custom_css, custom_js, published)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (final_slug, title, provider, url, tags, summary, body_html,
                 custom_css, custom_js, is_published),
            )
            course_id = cur.lastrowid
        else:
            conn.execute(
                """UPDATE courses SET slug=?, title=?, provider=?, url=?,
                   tags=?, summary=?, body_html=?, custom_css=?, custom_js=?,
                   published=?, updated_at=datetime('now') WHERE id=?""",
                (final_slug, title, provider, url, tags, summary, body_html,
                 custom_css, custom_js, is_published, course_id),
            )
    return RedirectResponse(f"/admin/courses/{course_id}/edit", status_code=303)


@router.post("/courses/{course_id}/delete")
def delete_course(course_id: int, user=Depends(require_admin)):
    with get_db() as conn:
        conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    return RedirectResponse("/admin/courses", status_code=303)


@router.get("/users")
def user_list(request: Request, user=Depends(require_admin)):
    with get_db() as conn:
        users = conn.execute(
            """SELECT u.*, COUNT(p.id) AS post_count
               FROM users u LEFT JOIN posts p ON p.user_id = u.id
               GROUP BY u.id ORDER BY u.created_at"""
        ).fetchall()
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {"users": users, "user": user, "reset_user": None, "temp_password": None},
    )


@router.post("/users/{user_id}/reset-password")
def reset_user_password(request: Request, user_id: int, user=Depends(require_admin)):
    temp_password = secrets.token_urlsafe(9)
    with get_db() as conn:
        target = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if target is None:
            raise HTTPException(status_code=404)
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(temp_password), user_id),
        )
        # Their old sessions are no longer trustworthy.
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        users = conn.execute(
            """SELECT u.*, COUNT(p.id) AS post_count
               FROM users u LEFT JOIN posts p ON p.user_id = u.id
               GROUP BY u.id ORDER BY u.created_at"""
        ).fetchall()
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {"users": users, "user": user,
         "reset_user": target["username"], "temp_password": temp_password},
    )


@router.post("/users/{user_id}/delete")
def delete_user(request: Request, user_id: int, user=Depends(require_admin)):
    with get_db() as conn:
        target = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if target is None:
            raise HTTPException(status_code=404)
        if target["is_admin"]:
            raise HTTPException(status_code=400, detail="Admins can't be deleted here.")
        # Their posts/threads survive with a "[deleted]" author
        # (user_id has ON DELETE SET NULL); sessions cascade away.
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/courses/preview", response_class=HTMLResponse)
def preview_course(
    request: Request,
    user=Depends(require_admin),
    title: str = Form(""),
    provider: str = Form(""),
    url: str = Form(""),
    tags: str = Form(""),
    body_html: str = Form(""),
    custom_css: str = Form(""),
    custom_js: str = Form(""),
):
    course = {
        "title": title or "Untitled course",
        "provider": provider,
        "url": url,
        "tags": tags,
        "custom_css": custom_css,
        "custom_js": custom_js,
    }
    return templates.TemplateResponse(
        request,
        "public/course_detail.html",
        {"course": course, "rendered_body": render_body(body_html), "active": "courses"},
    )
