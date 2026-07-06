from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["dateformat"] = lambda dt: f"{dt:%b} {dt.day}, {dt.year}"
templates.env.globals["site_url"] = settings.site_url
