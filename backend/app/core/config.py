import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Ensure .env is loaded even when config is imported early (e.g., via uvicorn reload)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))
load_dotenv()

class Settings(BaseModel):
    app_name: str = "Legal AI API"
    database_url: str = "sqlite:///./legal_ai.db"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def has_llm(self) -> bool:
        return bool(self.openai_api_key or self.gemini_api_key or self.groq_api_key)

settings = Settings()
