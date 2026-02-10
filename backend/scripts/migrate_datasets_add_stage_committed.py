#!/usr/bin/env python3
"""
Add stage and committed columns to datasets table if missing.
Works with both SQLite and MySQL. Run from backend: python scripts/migrate_datasets_add_stage_committed.py
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine

def has_column(conn, table: str, column: str) -> bool:
    dialect = engine.dialect.name
    if dialect == "sqlite":
        r = conn.execute(text(f"PRAGMA table_info({table})"))
        return any(row[1] == column for row in r.fetchall())
    if dialect in ("mysql", "pymysql"):
        r = conn.execute(text(f"SHOW COLUMNS FROM {table} LIKE :col"), {"col": column})
        return r.fetchone() is not None
    return False

def main():
    dialect = engine.dialect.name
    print(f"Database: {dialect}")

    with engine.begin() as conn:
        if not has_column(conn, "datasets", "stage"):
            conn.execute(text("ALTER TABLE datasets ADD COLUMN stage VARCHAR(20) NOT NULL DEFAULT 'DRAFT'"))
            print("[ok] Added column datasets.stage")
        else:
            print("[skip] datasets.stage already exists")

        if not has_column(conn, "datasets", "committed"):
            if dialect == "sqlite":
                conn.execute(text("ALTER TABLE datasets ADD COLUMN committed INTEGER NOT NULL DEFAULT 0"))
            else:
                conn.execute(text("ALTER TABLE datasets ADD COLUMN committed TINYINT(1) NOT NULL DEFAULT 0"))
            print("[ok] Added column datasets.committed")
        else:
            print("[skip] datasets.committed already exists")

    print("Done. Restart uvicorn if it is running.")


if __name__ == "__main__":
    main()
