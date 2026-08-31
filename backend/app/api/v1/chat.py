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

load_dotenv()

router = APIRouter(prefix="/chat", tags=["chat"])

class Query(BaseModel):
    document_id: int
    question: str

@router.get("/status")
def llm_status():
    """Check which LLM providers are configured and reachable."""
    load_dotenv(override=True)
    env_openai = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    groq_key = os.getenv("GROQ_API_KEY", "") or ""
    return {
        "openai_configured": bool(env_openai),
        "openai_source": "env",
        "gemini_configured": bool(gemini_key.strip()),
        "groq_configured": bool(groq_key.strip()),
        "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "fallback_available": True,
        "active_provider": "openai" if env_openai else ("gemini" if gemini_key.strip() else ("groq" if groq_key.strip() else "local_extract+ollama"))
    }

@router.post("")
def chat(q: Query, db: Session = Depends(get_db)):
    d = db.get(Document, q.document_id)
    if not d:
        raise HTTPException(404, "Document not found")
    a = answer(d.content, q.question)
    db.add(Conversation(document_id=d.id, question=q.question, answer=a))
    db.commit()
    return {"answer": a}

