from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.document import Document
from app.services.analysis_service import analyze
router=APIRouter(prefix="/analysis",tags=["analysis"])
@router.post("/{document_id}")
def run(document_id:int,db:Session=Depends(get_db)):
    d=db.get(Document,document_id)
    if not d: raise HTTPException(404,"Document not found")
    return analyze(d.content)
