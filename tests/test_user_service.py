"""Run with: python -m pytest tests/test_user_service.py -v

These tests need NO MySQL server: db_session is replaced by a small
in-memory SQLite stand-in that understands %s and dictionary cursors.
"""
import sqlite3
from contextlib import contextmanager

import pytest

from models import user_service as svc

SCHEMA = """
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student','teacher')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


class _Cursor:
    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, params=()):
        self._raw.execute(sql.replace("%s", "?"), params)

    def fetchone(self):
        row = self._raw.fetchone()
        return dict(row) if row is not None else None

    @property
    def lastrowid(self):
        return self._raw.lastrowid

    def close(self):
        self._raw.close()


class _Conn:
    def __init__(self, raw):
        self._raw = raw

    def cursor(self, dictionary=False):
        return _Cursor(self._raw.cursor())


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    raw = sqlite3.connect(":memory:")
    raw.row_factory = sqlite3.Row
    raw.execute(SCHEMA)

    @contextmanager
    def fake_session():
        yield _Conn(raw)
        raw.commit()

    monkeypatch.setattr(svc, "db_session", fake_session)
    monkeypatch.setattr(svc, "ITERATIONS", 1000)   # keep tests fast
    yield raw
    raw.close()


def test_student_can_register_and_login():
    svc.register_user("amina", "password123")
    user = svc.login_user("amina", "password123")
    assert user["username"] == "amina" and user["role"] == "student"


def test_wrong_password_rejected():
    svc.register_user("amina", "password123")
    with pytest.raises(svc.UserError):
        svc.login_user("amina", "wrongpass")


def test_unknown_user_rejected():
    with pytest.raises(svc.UserError):
        svc.login_user("ghost", "password123")


def test_duplicate_username_rejected():
    svc.register_user("amina", "password123")
    with pytest.raises(svc.UserError):
        svc.register_user("amina", "another-pass1")


def test_password_is_hashed(fake_db):
    svc.register_user("amina", "password123")
    stored = fake_db.execute("SELECT password_hash FROM users").fetchone()[0]
    assert "password123" not in stored
    assert stored.startswith("pbkdf2_sha256$")


def test_same_password_gets_different_hashes():
    assert svc.hash_password("password123") != svc.hash_password("password123")


def test_student_cannot_register_as_teacher():
    svc.register_user("amina", "password123")
    assert not svc.is_teacher(svc.login_user("amina", "password123"))
    with pytest.raises(TypeError):
        svc.register_user("sneaky", "password123", "teacher")


def test_teacher_account_has_teacher_privileges():
    svc.create_teacher_account("mr_otieno", "password123")
    assert svc.is_teacher(svc.login_user("mr_otieno", "password123"))


def test_short_username_and_password_rejected():
    with pytest.raises(svc.UserError):
        svc.register_user("ab", "password123")
    with pytest.raises(svc.UserError):
        svc.register_user("amina", "short")


def test_update_username():
    uid = svc.register_user("amina", "password123")
    svc.change_username(uid, "amina2")
    assert svc.get_profile(uid)["username"] == "amina2"


def test_cannot_change_to_taken_username():
    svc.register_user("amina", "password123")
    uid = svc.register_user("baraka", "password123")
    with pytest.raises(svc.UserError):
        svc.change_username(uid, "amina")


def test_change_password():
    uid = svc.register_user("amina", "password123")
    with pytest.raises(svc.UserError):
        svc.change_password(uid, "wrong-old", "newpassword456")
    svc.change_password(uid, "password123", "newpassword456")
    with pytest.raises(svc.UserError):
        svc.login_user("amina", "password123")
    assert svc.login_user("amina", "newpassword456")


def test_delete_requires_password_and_confirmation():
    uid = svc.register_user("amina", "password123")
    with pytest.raises(svc.UserError):
        svc.delete_account(uid, "wrong", "DELETE")
    with pytest.raises(svc.UserError):
        svc.delete_account(uid, "password123", "no")
    svc.delete_account(uid, "password123", "DELETE")
    with pytest.raises(svc.UserError):
        svc.login_user("amina", "password123")


# ---------- menu behaviour (registration prompt, logout handoff) ----------
def _feed(monkeypatch, inputs, secrets=()):
    from ui import auth_menu
    it, st = iter(inputs), iter(secrets)
    monkeypatch.setattr("builtins.input", lambda _="": next(it))
    monkeypatch.setattr(auth_menu, "getpass", lambda _="": next(st))
    monkeypatch.setattr("ui.terminal.clear_screen", lambda: None)
    return auth_menu


def test_registration_prompt_has_no_role_choice_and_creates_student(monkeypatch, capsys):
    menu = _feed(monkeypatch, ["amina"], ["password123", "password123"])
    menu.register_screen()
    out = capsys.readouterr().out.lower()
    assert "teacher" not in out and "role" not in out
    assert svc.login_user("amina", "password123")["role"] == "student"


def test_register_screen_shows_readable_errors(monkeypatch, capsys):
    svc.register_user("amina", "password123")
    menu = _feed(monkeypatch, ["amina"], ["password123", "password123"])
    menu.register_screen()
    assert "already taken" in capsys.readouterr().out
    menu = _feed(monkeypatch, ["ab"], ["password123", "password123"])
    menu.register_screen()
    assert "3-30 characters" in capsys.readouterr().out


def test_logout_returns_none(monkeypatch, capsys):
    menu = _feed(monkeypatch, ["5"])
    user = {"user_id": 1, "username": "amina", "role": "student"}
    assert menu.account_menu(user) is None
    assert "logged out" in capsys.readouterr().out


def test_back_keeps_user_logged_in(monkeypatch):
    menu = _feed(monkeypatch, ["0"])
    user = {"user_id": 1, "username": "amina", "role": "student"}
    assert menu.account_menu(user) == user
