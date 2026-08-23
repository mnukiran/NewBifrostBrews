from fastapi import APIRouter, HTTPException, Request

from app.db import get_db
from app.services.content import render_body
from app.templating import templates

router = APIRouter()


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "public/home.html", {"active": "home"})


@router.get("/courses")
def courses(request: Request):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT slug, title, provider, tags, summary FROM courses "
            "WHERE published = 1 ORDER BY updated_at DESC"
        ).fetchall()
    return templates.TemplateResponse(
        request,
        "public/courses.html",
        {"active": "courses", "courses": rows, "wide": True},
    )


@router.get("/courses/{slug}")
def course_detail(request: Request, slug: str):
    with get_db() as conn:
        course = conn.execute(
            "SELECT * FROM courses WHERE slug = ? AND published = 1", (slug,)
        ).fetchone()
    if course is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request,
        "public/course_detail.html",
        {
            "active": "courses",
            "course": course,
            "rendered_body": render_body(course["body_html"]),
        },
    )


@router.get("/about")
def about(request: Request):
    return templates.TemplateResponse(request, "public/about.html", {"active": "about"})
