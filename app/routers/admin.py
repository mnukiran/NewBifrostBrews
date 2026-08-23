import re
import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db import get_db
from app.routers.auth import SESSION_COOKIE
from app.security import get_session_user
from app.services.content import render_body
from app.templating import templates

router = APIRouter(prefix="/admin")


def require_admin(request: Request) -> sqlite3.Row:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with get_db() as conn:
            user = get_session_user(conn, token)
        if user is not None and user["is_admin"]:
            return user
    raise HTTPException(status_code=303, headers={"Location": "/admin/login"})


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
