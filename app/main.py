from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from starlette.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.db import init_db
from app.routers import admin, auth, public


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Bifrost Brews", docs_url=None, redoc_url=None, lifespan=lifespan)

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
app.include_router(auth.router)
app.include_router(admin.router)
