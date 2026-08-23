from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.db import get_db
from app.security import create_session, delete_session, verify_password
from app.templating import templates

router = APIRouter()

SESSION_COOKIE = "session"


@router.get("/admin/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "admin/login.html", {"error": None})


@router.post("/admin/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_admin = 1", (username,)
        ).fetchone()
        if user is None or not verify_password(password, user["password_hash"]):
            return templates.TemplateResponse(
                request,
                "admin/login.html",
                {"error": "Wrong username or password."},
                status_code=401,
            )
        token = create_session(conn, user["id"])
    response = RedirectResponse("/admin/courses", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/admin/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with get_db() as conn:
            delete_session(conn, token)
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response
