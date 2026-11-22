"""Accounts, authentication and account management (Keji).

Uses the team's shared helper:  from db.connection import db_session
(db_session is expected to commit on success, like the other services).
Table used: users(user_id, username, password_hash, role, created_at).
"""
import hashlib
import hmac
import os

try:
    from db.connection import db_session
except ModuleNotFoundError:   # db module not merged yet; tests patch this
    def db_session():
        raise NotImplementedError("db.connection not implemented yet")

ITERATIONS = 200_000
MIN_USERNAME = 3          # matches chk_users_username_length in schema.sql
MAX_USERNAME = 30
MIN_PASSWORD = 8


class UserError(ValueError):
    """Any user-facing account problem (bad input, wrong password...)."""


# ---------- password security ----------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters)
        )
    except (ValueError, TypeError, AttributeError):
        return False
    return hmac.compare_digest(digest.hex(), hash_hex)


# ---------- validation ----------
def _clean_username(username) -> str:
    username = (username or "").strip()
    if not MIN_USERNAME <= len(username) <= MAX_USERNAME:
        raise UserError(
            f"Username must be {MIN_USERNAME}-{MAX_USERNAME} characters long."
        )
    return username


def _check_new_password(password) -> None:
    if not password or len(password) < MIN_PASSWORD:
        raise UserError(f"Password must be at least {MIN_PASSWORD} characters.")


def _is_integrity_error(exc) -> bool:
    return type(exc).__name__ == "IntegrityError"   # mysql / sqlite


# ---------- internal helpers ----------
def _fetch_one(sql, params):
    with db_session() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(sql, params)
            return cur.fetchone()
        finally:
            cur.close()


def _execute(sql, params):
    with db_session() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            return cur.lastrowid
        finally:
            cur.close()


def _insert_user(username, password, role) -> int:
    username = _clean_username(username)
    _check_new_password(password)
    if _fetch_one("SELECT user_id FROM users WHERE username = %s", (username,)):
        raise UserError("That username is already taken.")
    try:
        return _execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, hash_password(password), role),
        )
    except Exception as exc:                      # race: duplicate slipped through
        if _is_integrity_error(exc):
            raise UserError("That username is already taken.") from exc
        raise


# ---------- registration ----------
def register_user(username: str, password: str) -> int:
    """Public registration. The role is ALWAYS 'student'; there is no role
    argument, so nobody can register themselves as a teacher."""
    return _insert_user(username, password, "student")


def create_teacher_account(username: str, password: str) -> int:
    """Only called by scripts/create_teacher.py (guarded by an admin code)."""
    return _insert_user(username, password, "teacher")


# ---------- login ----------
def login_user(username: str, password: str) -> dict:
    row = _fetch_one(
        "SELECT user_id, username, password_hash, role FROM users WHERE username = %s",
        ((username or "").strip(),),
    )
    # Same message for unknown user and wrong password (no user enumeration).
    if row is None or not verify_password(password or "", row["password_hash"]):
        raise UserError("Invalid username or password.")
    return {"user_id": row["user_id"], "username": row["username"], "role": row["role"]}


def is_teacher(user: dict) -> bool:
    return bool(user) and user.get("role") == "teacher"


# ---------- account CRUD ----------
def get_profile(user_id: int) -> dict:
    row = _fetch_one(
        "SELECT user_id, username, role, created_at FROM users WHERE user_id = %s",
        (user_id,),
    )
    if row is None:
        raise UserError("User not found.")
    return row


def change_username(user_id: int, new_username: str) -> None:
    new_username = _clean_username(new_username)
    taken = _fetch_one(
        "SELECT user_id FROM users WHERE username = %s AND user_id <> %s",
        (new_username, user_id),
    )
    if taken:
        raise UserError("That username is already taken.")
    try:
        _execute("UPDATE users SET username = %s WHERE user_id = %s", (new_username, user_id))
    except Exception as exc:
        if _is_integrity_error(exc):
            raise UserError("That username is already taken.") from exc
        raise


def _require_password(user_id: int, password: str) -> None:
    row = _fetch_one("SELECT password_hash FROM users WHERE user_id = %s", (user_id,))
    if row is None or not verify_password(password or "", row["password_hash"]):
        raise UserError("Incorrect password.")


def change_password(user_id: int, old_password: str, new_password: str) -> None:
    _require_password(user_id, old_password)
    _check_new_password(new_password)
    _execute(
        "UPDATE users SET password_hash = %s WHERE user_id = %s",
        (hash_password(new_password), user_id),
    )


def delete_account(user_id: int, password: str, confirmation: str) -> None:
    """Re-authenticate with the password AND type DELETE to confirm."""
    _require_password(user_id, password)
    if (confirmation or "").strip() != "DELETE":
        raise UserError("Deletion not confirmed. Type DELETE to confirm.")
    _execute("DELETE FROM users WHERE user_id = %s", (user_id,))
