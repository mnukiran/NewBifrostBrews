from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Setting
from app.services import content
from app.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    data = content.get_home_data(db)
    return templates.TemplateResponse(request, "public/home.html", data)


@router.get("/articles", response_class=HTMLResponse)
def article_list(request: Request, page: int = 1, db: Session = Depends(get_db)):
    page_obj = content.list_articles(db, page=page)
    return templates.TemplateResponse(
        request, "public/article_list.html", {"page_obj": page_obj}
    )


@router.get("/articles/{slug}", response_class=HTMLResponse)
def article_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    post = content.get_article_by_slug(db, slug)
    if post is None:
        return templates.TemplateResponse(
            request, "public/404.html", {}, status_code=404
        )
    content.record_view(db, "post", post)
    related = content.related_posts_by_tag(db, post)
    return templates.TemplateResponse(
        request, "public/article_detail.html", {"post": post, "related": related}
    )


@router.get("/recipes", response_class=HTMLResponse)
def recipe_list(
    request: Request,
    page: int = 1,
    style: str | None = None,
    difficulty: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    page_obj = content.list_recipes(
        db, page=page, style=style, difficulty=difficulty, tag_slug=tag
    )
    return templates.TemplateResponse(
        request,
        "public/recipe_list.html",
        {
            "page_obj": page_obj,
            "selected_style": style,
            "selected_difficulty": difficulty,
        },
    )


@router.get("/recipes/{slug}", response_class=HTMLResponse)
def recipe_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    recipe = content.get_recipe_by_slug(db, slug)
    if recipe is None:
        return templates.TemplateResponse(
            request, "public/404.html", {}, status_code=404
        )
    content.record_view(db, "recipe", recipe)
    return templates.TemplateResponse(
        request, "public/recipe_detail.html", {"recipe": recipe}
    )


@router.get("/tags/{slug}", response_class=HTMLResponse)
def tag_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    tag = content.get_tag_by_slug(db, slug)
    if tag is None:
        return templates.TemplateResponse(
            request, "public/404.html", {}, status_code=404
        )
    items = content.content_for_tag(db, tag)
    return templates.TemplateResponse(
        request, "public/tag.html", {"tag": tag, "items": items}
    )


@router.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = "", db: Session = Depends(get_db)):
    results = content.search(db, q) if q else []
    return templates.TemplateResponse(
        request, "public/search.html", {"query": q, "results": results}
    )


@router.get("/search/partial", response_class=HTMLResponse)
def search_partial(request: Request, q: str = "", db: Session = Depends(get_db)):
    results = content.search(db, q) if q else []
    return templates.TemplateResponse(
        request, "partials/_search_results.html", {"query": q, "results": results}
    )


@router.get("/about", response_class=HTMLResponse)
def about(request: Request, db: Session = Depends(get_db)):
    about_html = db.scalar(select(Setting.value).where(Setting.key == "about_html"))
    return templates.TemplateResponse(
        request, "public/about.html", {"about_html": about_html or ""}
    )
