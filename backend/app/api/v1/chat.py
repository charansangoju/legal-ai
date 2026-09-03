import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.db.session import get_db
from app.db.models.document import Document
from app.db.models.conversation import Conversation
from app.services.chat_service import answer

load_dotenv(override=False)

router = APIRouter(prefix="/chat", tags=["chat"])

class Query(BaseModel):
    document_id: int
    question: str

@router.get("/status")
def llm_status():
    """Check which LLM providers are configured and reachable."""
    # Don't override Vercel env - check without reload, or reload without override
    load_dotenv(override=False)
    env_openai = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    groq_key = os.getenv("GROQ_API_KEY", "") or ""
    return {
        "openai_configured": bool(env_openai and env_openai != "your_openai_api_key_here"),
        "openai_key_prefix": (env_openai[:8] + "...") if env_openai else None,
        "openai_source": "env" if env_openai else "none",
        "gemini_configured": bool(gemini_key.strip()),
        "groq_configured": bool(groq_key.strip()),
        "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "fallback_available": True,
        "active_provider": "openai" if (env_openai and env_openai != "your_openai_api_key_here") else ("gemini" if gemini_key.strip() else ("groq" if groq_key.strip() else "local_extract+ollama")),
        "hint": "Set OPENAI_API_KEY in Vercel Environment Variables or pass X-OpenAI-Key header" if not env_openai or env_openai == "your_openai_api_key_here" else None
    }

@router.post("")
def chat(q: Query, db: Session = Depends(get_db), x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"), authorization: Optional[str] = Header(None)):
    d = db.get(Document, q.document_id)
    if not d:
        raise HTTPException(404, "Document not found")
    # Allow per-request API key via header (for frontend 🔑 button or custom key)
    # Precedence: Header X-OpenAI-Key > Authorization Bearer > env
    header_key = None
    if x_openai_key:
        header_key = x_openai_key.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        # Only use Bearer as OpenAI key if it looks like sk-*
        maybe = authorization[7:].strip()
        if maybe.startswith("sk-"):
            header_key = maybe
    a = answer(d.content, q.question, api_key=header_key)
    db.add(Conversation(document_id=d.id, question=q.question, answer=a))
    db.commit()
    return {"answer": a}

