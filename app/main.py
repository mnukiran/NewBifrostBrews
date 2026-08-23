from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from starlette.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.routers import public

app = FastAPI(title="Bifrost Brews", docs_url=None, redoc_url=None)

app.add_middleware(GZipMiddleware, minimum_size=500)


class CachedStaticFiles(StaticFiles):
    """Static assets are referenced with ?v=ASSET_VERSION, so they can be
    cached forever; bumping the version busts the cache."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


app.mount("/static", CachedStaticFiles(directory=STATIC_DIR), name="static")

app.include_router(public.router)
