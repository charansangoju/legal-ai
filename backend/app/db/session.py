import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


database_url = settings.database_url

# Convert standard PostgreSQL URLs to the psycopg SQLAlchemy driver.
if database_url.startswith("postgres://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]

elif database_url.startswith("postgresql://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]


# SQLite and PostgreSQL require different connection settings.
if database_url.startswith("sqlite"):
    # On Vercel the filesystem is read-only except /tmp, so ./legal_ai.db
    # would raise "unable to open database file". Use /tmp as fallback
    # if SQLite is somehow still used on Vercel (safety net).
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("VERCEL_URL"):
        if database_url == "sqlite:///./legal_ai.db":
            database_url = "sqlite:////tmp/legal_ai.db"
        elif database_url.startswith("sqlite:///./"):
            database_url = database_url.replace("sqlite:///./", "sqlite:////tmp/")
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
else:
    # Neon/serverless PostgreSQL works better without a persistent
    # SQLAlchemy connection pool.
    engine = create_engine(
        database_url,
        poolclass=NullPool,
        pool_pre_ping=True,
    )


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
