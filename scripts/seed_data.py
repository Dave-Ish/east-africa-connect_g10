"""Load sample data. Usage: python scripts/seed_data.py [db_path]

Runs db/schema.sql (if present) then db/seed.sql against a SQLite file
(default: app.db).
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_sql_file(conn, path):
    if path.exists():
        conn.executescript(path.read_text(encoding="utf-8"))
        print(f"Loaded {path.relative_to(ROOT)}")
        return True
    return False


def main(db_path="app.db"):
    conn = sqlite3.connect(db_path)
    try:
        run_sql_file(conn, ROOT / "db" / "schema.sql")
        if not run_sql_file(conn, ROOT / "db" / "seed.sql"):
            print("db/seed.sql not found - nothing to load.")
            return 1
        conn.commit()
    finally:
        conn.close()
    print(f"Sample data ready in {db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
