"""Seed the shared East Africa Connect language catalog.

This script is intentionally idempotent: it can be run repeatedly by each
developer after the schema exists without creating duplicate language rows.
It writes directly to MySQL using parameterized SQL; no CSV or JSON files are
used for application data.

Run from the repository root after setting the MYSQL_* environment variables:

    python -m scripts.seed_data
"""

from __future__ import annotations

from db.connection import db_session, init_db


LANGUAGES = (
    ("kin", "Kinyarwanda"),
    ("swa", "Swahili"),
    ("fra", "French"),
    ("eng", "English"),
)


def seed_languages() -> int:
    """Insert or reactivate the four supported languages."""
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.executemany(
                """
                INSERT INTO languages (language_code, language_name, is_active)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    language_name = VALUES(language_name),
                    is_active = VALUES(is_active)
                """,
                [(code, name, 1) for code, name in LANGUAGES],
            )
            return len(LANGUAGES)
        finally:
            cursor.close()


def main() -> None:
    database = init_db()
    count = seed_languages()
    print(f"Database ready: {database}")
    print(f"Seeded/reactivated {count} supported languages:")
    for code, name in LANGUAGES:
        print(f"  - {name} ({code})")


if __name__ == "__main__":
    main()
