from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db import SessionLocal
from app.models import Redirect
from app.routers import public
from app.templating import templates

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    app = FastAPI(title="Bifrost Brews")

    app.mount(
        "/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static"
    )

    app.include_router(public.router)

    @app.exception_handler(StarletteHTTPException)
    async def not_found_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            db = SessionLocal()
            try:
                redirect = db.scalar(
                    select(Redirect).where(Redirect.old_path == request.url.path)
                )
            finally:
                db.close()
            if redirect:
                return RedirectResponse(redirect.new_path, status_code=301)
            return templates.TemplateResponse(
                request, "public/404.html", {}, status_code=404
            )
        raise exc

    return app


app = create_app()
