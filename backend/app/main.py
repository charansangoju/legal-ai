import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.db.session import Base, engine
from app.db.models import document, analysis, translation, conversation
from app.api.v1 import (
    documents,
    analysis as analysis_api,
    chat,
    auth,
    translation as translation_api,
    summarization,
    speech,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup without crashing the import.
    # This avoids `sqlite3.OperationalError: unable to open database file`
    # on Vercel where the filesystem is read-only and SQLite is not usable.
    # On Vercel, DATABASE_URL must be a PostgreSQL/Neon URL (validated in
    # app.core.config). Failures here are logged, not raised, so the
    # serverless function can still start and return a meaningful error
    # instead of a crash during module import.
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
    yield


app = FastAPI(title="Legal AI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in [
    documents.router,
    analysis_api.router,
    chat.router,
    auth.router,
    translation_api.router,
    summarization.router,
    speech.router,
]:
    app.include_router(r, prefix="/api/v1")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "legal-ai",
    }


@app.get("/api/v1/health")
def api_health():
    """Health check that also verifies DB connectivity."""
    try:
        from sqlalchemy import text
        from app.db.session import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        logger.warning(f"Health DB check failed: {e}")
        return {"status": "ok", "db": "disconnected", "error": str(e)}
