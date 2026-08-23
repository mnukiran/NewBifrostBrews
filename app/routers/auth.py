import re

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.config import INVITE_CODE
from app.db import get_db
from app.security import create_session, delete_session, hash_password, verify_password
from app.templating import templates

router = APIRouter()

SESSION_COOKIE = "session"
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


def safe_next(next_url: str) -> str:
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return "/"


def login_response(token: str, next_url: str) -> RedirectResponse:
    response = RedirectResponse(safe_next(next_url), status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/login")
def login_form(request: Request, next: str = "/"):
    return templates.TemplateResponse(
        request, "auth/login.html", {"error": None, "next": safe_next(next)}
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
                {"error": "Wrong username or password.", "next": safe_next(next)},
                status_code=401,
            )
        token = create_session(conn, user["id"])
    return login_response(token, next)


@router.get("/signup")
def signup_form(request: Request):
    return templates.TemplateResponse(
        request,
        "auth/signup.html",
        {"error": None, "invite_required": bool(INVITE_CODE)},
    )


@router.post("/signup")
def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    invite_code: str = Form(""),
):
    def fail(message: str, status: int = 400):
        return templates.TemplateResponse(
            request,
            "auth/signup.html",
            {"error": message, "invite_required": bool(INVITE_CODE)},
            status_code=status,
        )

    if INVITE_CODE and invite_code.strip() != INVITE_CODE:
        return fail("Invalid invite code.", status=403)
    if not USERNAME_RE.match(username):
        return fail("Username must be 3–30 characters: letters, digits, underscores.")
    if len(password) < 8:
        return fail("Password must be at least 8 characters.")
    if password != password_confirm:
        return fail("Passwords don't match.")

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
    return login_response(token, "/forum")


@router.post("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with get_db() as conn:
            delete_session(conn, token)
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response
