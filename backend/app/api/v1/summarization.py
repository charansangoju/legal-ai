from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.document import Document
from app.services.summarization_service import run
router=APIRouter(prefix="/summarization",tags=["summarization"])
@router.get("/{document_id}")
def summarize(document_id:int,db:Session=Depends(get_db)):
    d=db.get(Document,document_id)
    if not d: raise HTTPException(404,"Document not found")
    return {"summary":run(d.content)}
