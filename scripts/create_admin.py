"""Create (or reset the password of) the admin account.

Usage: python scripts/create_admin.py <username> <password>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_db, init_db
from app.security import hash_password


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: create_admin.py <username> <password>")
    username, password = sys.argv[1], sys.argv[2]
    if len(password) < 8:
        sys.exit("password must be at least 8 characters")
    init_db()
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE users SET password_hash = ?, is_admin = 1 WHERE id = ?",
                (hash_password(password), existing["id"]),
            )
            print(f"password reset for admin '{username}'")
        else:
            conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
                (username, hash_password(password)),
            )
            print(f"admin '{username}' created")


if __name__ == "__main__":
    main()
