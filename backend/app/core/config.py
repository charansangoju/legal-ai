import os

from dotenv import load_dotenv
from pydantic import BaseModel


# Load local .env files when running locally.
load_dotenv(
    dotenv_path=os.path.join(
        os.path.dirname(__file__),
        "../../../.env"
    )
)
load_dotenv()


def _is_vercel() -> bool:
    """Robust Vercel detection - checks multiple env vars set by Vercel."""
    return bool(
        os.getenv("VERCEL")
        or os.getenv("VERCEL_ENV")
        or os.getenv("VERCEL_URL")
        or os.getenv("VERCEL_PROJECT_ID")
    )


def get_database_url() -> str:
    """
    Get the PostgreSQL connection string from the deployment environment.

    Supports:
    - DATABASE_URL
    - POSTGRES_URL
    - POSTGRES_URL_NON_POOLING
    - POSTGRES_PRISMA_URL

    SQLite is used only for local development.
    On Vercel, PostgreSQL (Neon) is required because the filesystem is
    read-only and ephemeral (except /tmp), so SQLite is not persistent.
    """

    database_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRES_URL_NON_POOLING")
        or os.getenv("POSTGRES_PRISMA_URL")
    )

    if database_url:
        return database_url.strip().strip('"').strip("'")

    # Local development fallback.
    if not _is_vercel():
        return "sqlite:///./legal_ai.db"

    # Never silently fall back to SQLite on Vercel.
    raise RuntimeError(
        "DATABASE_URL is not configured in the Vercel environment. "
        "Add your Neon PostgreSQL connection string to Vercel Environment Variables."
    )


class Settings(BaseModel):
    app_name: str = "Legal AI API"

    database_url: str = get_database_url()

    openai_api_key: str = os.getenv(
        "OPENAI_API_KEY",
        ""
    )

    gemini_api_key: str = (
        os.getenv("GEMINI_API_KEY", "")
        or os.getenv("GOOGLE_API_KEY", "")
    )

    groq_api_key: str = os.getenv(
        "GROQ_API_KEY",
        ""
    )

    ollama_host: str = os.getenv(
        "OLLAMA_HOST",
        "http://localhost:11434"
    )

    def has_llm(self) -> bool:
        return bool(
            self.openai_api_key
            or self.gemini_api_key
            or self.groq_api_key
        )


settings = Settings()
