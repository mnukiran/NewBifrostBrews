from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.config import ASSET_VERSION, SITE_NAME, TAGLINE, TEMPLATES_DIR

router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals.update(
    site_name=SITE_NAME,
    tagline=TAGLINE,
    asset_v=ASSET_VERSION,
)


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "public/home.html", {"active": "home"})


@router.get("/courses")
def courses(request: Request):
    return templates.TemplateResponse(request, "public/courses.html", {"active": "courses"})


@router.get("/forum")
def forum(request: Request):
    return templates.TemplateResponse(request, "public/forum.html", {"active": "forum"})


@router.get("/about")
def about(request: Request):
    return templates.TemplateResponse(request, "public/about.html", {"active": "about"})
