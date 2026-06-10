#!/usr/bin/env python3
"""Verify Supabase/Postgres connectivity and schema readiness."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

for env_file in (ROOT / ".env", BACKEND / ".env"):
    if not env_file.exists():
        continue
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url or "[PASSWORD]" in database_url or "[PROJECT_REF]" in database_url:
        print("FAIL: DATABASE_URL is missing or still contains placeholders.")
        return 1

    from sqlalchemy import create_engine, text

    connect_args: dict = {}
    if "supabase.com" in database_url and "sslmode=" not in database_url:
        connect_args["sslmode"] = "require"

    engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            tables = conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' ORDER BY tablename"
                )
            ).fetchall()
            counts = {}
            for (table,) in tables:
                counts[table] = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    except Exception as exc:
        print(f"FAIL: could not connect to Supabase/Postgres ({exc.__class__.__name__})")
        return 1

    print("OK: Supabase connection successful")
    print(f"Tables: {', '.join(counts) if counts else '(none)'}")
    for table, count in counts.items():
        print(f"  - {table}: {count} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
