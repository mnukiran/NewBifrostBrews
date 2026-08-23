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


def login_response(token: str, next_url: str, message: str) -> RedirectResponse:
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
        {"error": None, "next": next, "username": ""},
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
            return templates.TemplateResponse(
                request,
                "auth/login.html",
                {"error": "Wrong username or password.",
                 "next": safe_next(next), "username": username},
                status_code=401,
            )
        token = create_session(conn, user["id"])
    return login_response(token, next, f"Welcome back, {user['username']}.")


@router.get("/signup")
def signup_form(request: Request, next: str = "/forum"):
    next = safe_next(next)
    if request.state.user is not None:
        return RedirectResponse(next, status_code=303)
    return templates.TemplateResponse(
        request,
        "auth/signup.html",
        {"error": None, "invite_required": bool(INVITE_CODE),
         "next": next, "username": ""},
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
        return templates.TemplateResponse(
            request,
            "auth/signup.html",
            {"error": message, "invite_required": bool(INVITE_CODE),
             "next": safe_next(next), "username": username},
            status_code=status,
        )

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
        token, next, f"Welcome to Bifrost Brews, {username} — your account is ready."
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
