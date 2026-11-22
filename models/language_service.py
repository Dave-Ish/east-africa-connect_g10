"""Read operations for the application's language catalog."""

from __future__ import annotations

from typing import Any

try:
    from db.connection import db_session
except ModuleNotFoundError as exc:
    if exc.name != "db.connection":
        raise
    from db.connections import db_session


def _language_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Return schema field names alongside aliases expected by the UI."""
    language_id = row["language_id"]
    language_name = row["language_name"]
    language_code = row["language_code"]
    return {
        "language_id": language_id,
        "language_name": language_name,
        "language_code": language_code,
        "is_active": row["is_active"],
        "id": language_id,
        "name": language_name,
        "code": language_code,
    }


def list_active_languages() -> list[dict]:
    """Return active languages sorted by name, with database and UI keys."""
    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT language_id, language_name, language_code, is_active
                FROM languages
                WHERE is_active = %s
                ORDER BY language_name, language_id
                """,
                (1,),
            )
            rows = cursor.fetchall()
            return [_language_dict(row) for row in rows]
        finally:
            cursor.close()


def get_language(language_id: int) -> dict | None:
    """Return one language by ID, or None when no matching row exists.

    ``language_id`` must be a positive integer; invalid values raise ValueError.
    Inactive languages can also be retrieved through this direct lookup.
    """
    if isinstance(language_id, bool) or not isinstance(language_id, int) or language_id <= 0:
        raise ValueError("language_id must be a positive integer.")

    with db_session() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT language_id, language_name, language_code, is_active
                FROM languages
                WHERE language_id = %s
                """,
                (language_id,),
            )
            row = cursor.fetchone()
            return _language_dict(row) if row is not None else None
        finally:
            cursor.close()
