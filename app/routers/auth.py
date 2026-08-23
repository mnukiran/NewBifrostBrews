import re
from urllib.parse import quote, urlencode

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, Response

from app.config import COOKIE_SECURE, INVITE_CODE
from app.db import get_db
from app.security import create_session, delete_session, hash_password, verify_password
from app.templating import templates

router = APIRouter()

SESSION_COOKIE = "session"
FLASH_COOKIE = "flash"
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


def safe_next(next_url: str) -> str:
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return "/"


def flash(response: Response, message: str) -> None:
    response.set_cookie(
        FLASH_COOKIE, quote(message), max_age=30, httponly=True,
        samesite="lax", secure=COOKIE_SECURE,
    )


def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def login_response(request: Request, token: str, next_url: str, message: str) -> Response:
    if is_htmx(request):
        # htmx submit: cookies ride on this response, HX-Redirect makes
        # the browser do a full navigation to the destination.
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = safe_next(next_url)
    else:
        response = RedirectResponse(safe_next(next_url), status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )
    flash(response, message)
    return response


def auth_error(
    request: Request, mode: str, error: str, next_url: str, username: str,
    status: int,
):
    context = {
        "mode": mode,
        "error": error,
        "next": safe_next(next_url),
        "username": username,
        "invite_required": bool(INVITE_CODE),
    }
    if is_htmx(request):
        # 200 so htmx swaps the card in place with the error shown.
        return templates.TemplateResponse(
            request, "auth/_auth_card.html", context
        )
    template = "auth/login.html" if mode == "login" else "auth/signup.html"
    return templates.TemplateResponse(request, template, context, status_code=status)


def validate_new_password(password: str, password_confirm: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if password != password_confirm:
        return "Passwords don't match."
    return None


@router.get("/login")
def login_form(request: Request, next: str = "/"):
    next = safe_next(next)
    if request.state.user is not None:
        return RedirectResponse(next, status_code=303)
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"mode": "login", "error": None, "next": next, "username": "",
         "invite_required": bool(INVITE_CODE)},
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
):
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user is None or not verify_password(password, user["password_hash"]):
            return auth_error(
                request, "login", "Wrong username or password.",
                next, username, status=401,
            )
        token = create_session(conn, user["id"])
    return login_response(request, token, next, f"Welcome back, {user['username']}.")


@router.get("/signup")
def signup_form(request: Request, next: str = "/forum"):
    next = safe_next(next)
    if request.state.user is not None:
        return RedirectResponse(next, status_code=303)
    return templates.TemplateResponse(
        request,
        "auth/signup.html",
        {"mode": "signup", "error": None, "next": next, "username": "",
         "invite_required": bool(INVITE_CODE)},
    )


@router.post("/signup")
def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    invite_code: str = Form(""),
    next: str = Form("/forum"),
):
    def fail(message: str, status: int = 400):
        return auth_error(request, "signup", message, next, username, status)

    if INVITE_CODE and invite_code.strip() != INVITE_CODE:
        return fail("Invalid invite code.", status=403)
    if not USERNAME_RE.match(username):
        return fail("Username must be 3–30 characters: letters, digits, underscores.")
    error = validate_new_password(password, password_confirm)
    if error:
        return fail(error)

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            return fail("That username is taken.")
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 0)",
            (username, hash_password(password)),
        )
        token = create_session(conn, cur.lastrowid)
    return login_response(
        request, token, next,
        f"Welcome to Bifrost Brews, {username} — your account is ready.",
    )


@router.post("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with get_db() as conn:
            delete_session(conn, token)
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    flash(response, "You're logged out.")
    return response


@router.get("/account")
def account(request: Request):
    user = request.state.user
    if user is None:
        return RedirectResponse(
            f"/login?{urlencode({'next': '/account'})}", status_code=303
        )
    return templates.TemplateResponse(
        request, "auth/account.html", {"error": None, "user": user}
    )


@router.post("/account/password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    user = request.state.user
    if user is None:
        return RedirectResponse("/login?next=/account", status_code=303)

    error = None
    if not verify_password(current_password, user["password_hash"]):
        error = "Current password is wrong."
    else:
        error = validate_new_password(password, password_confirm)
    if error:
        return templates.TemplateResponse(
            request, "auth/account.html", {"error": error, "user": user},
            status_code=400,
        )

    current_token = request.cookies.get(SESSION_COOKIE)
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(password), user["id"]),
        )
        # Log out this user's other devices/sessions, keep this one.
        conn.execute(
            "DELETE FROM sessions WHERE user_id = ? AND token != ?",
            (user["id"], current_token or ""),
        )
    response = RedirectResponse("/account", status_code=303)
    flash(response, "Password updated. Other devices were logged out.")
    return response
