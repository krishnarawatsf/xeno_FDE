from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")
_is_supabase = "supabase.com" in settings.database_url or "pooler.supabase.com" in settings.database_url

_connect_args: dict = {}
if _is_sqlite:
    _connect_args["check_same_thread"] = False
elif _is_supabase and "sslmode=" not in settings.database_url:
    _connect_args["sslmode"] = "require"

_engine_kwargs: dict = {
    "connect_args": _connect_args,
    "pool_pre_ping": not _is_sqlite,
}
# Supabase transaction pooler (port 6543) works best with NullPool for serverless/long-lived apps
if _is_supabase and ":6543" in settings.database_url:
    _engine_kwargs["poolclass"] = NullPool

engine = create_engine(settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
