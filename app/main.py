from contextlib import asynccontextmanager
from urllib.parse import unquote

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from starlette.concurrency import run_in_threadpool
from starlette.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.db import get_db, init_db
from app.routers import admin, auth, forum, public
from app.security import get_session_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Bifrost Brews", docs_url=None, redoc_url=None, lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=500)


def _lookup_user(token: str):
    with get_db() as conn:
        return get_session_user(conn, token)


@app.middleware("http")
async def attach_current_user(request: Request, call_next):
    request.state.user = None
    request.state.flash = None
    request.state.is_guest = False
    if not request.url.path.startswith("/static"):
        token = request.cookies.get(auth.SESSION_COOKIE)
        if token:
            request.state.user = await run_in_threadpool(_lookup_user, token)
        if request.state.user is None:
            request.state.is_guest = bool(request.cookies.get(auth.GUEST_COOKIE))
        raw_flash = request.cookies.get(auth.FLASH_COOKIE)
        if raw_flash:
            request.state.flash = unquote(raw_flash)
    response = await call_next(request)
    # A flash message is shown once: the page render that consumed it
    # also clears the cookie.
    sets_new_flash = any(
        h.startswith(auth.FLASH_COOKIE + "=")
        for h in response.headers.getlist("set-cookie")
    )
    if request.state.flash is not None and not sets_new_flash:
        response.delete_cookie(auth.FLASH_COOKIE)
    return response


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
app.include_router(forum.router)
