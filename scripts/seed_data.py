"""Load sample data into the team's MySQL database.

Usage: python3 scripts/seed_data.py

Needs the same environment variables as connections.py (MYSQL_* settings).
Runs db/schema.sql first (via init_db), then db/seed.sql.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from connections import db_session, init_db  # noqa: E402

SEED_PATH = ROOT / "db" / "seed.sql"


def main():
    if not SEED_PATH.exists():
        print("db/seed.sql not found - nothing to load.")
        return 1

    database = init_db()
    print(f"Schema applied to database '{database}'.")

    sql = SEED_PATH.read_text(encoding="utf-8")
    statements = [s.strip() for s in sql.split(";") if s.strip()]

    with db_session() as conn:
        cursor = conn.cursor()
        try:
            for statement in statements:
                cursor.execute(statement)
            conn.commit()
        finally:
            cursor.close()

    print(f"Loaded {len(statements)} statements from db/seed.sql.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
