from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.document import Document
from app.services.translation_service import run
router=APIRouter(prefix="/translation",tags=["translation"])
class Request(BaseModel): document_id:int; target_language:str
@router.post("")
def translate(req:Request,db:Session=Depends(get_db)):
    d=db.get(Document,req.document_id)
    if not d: raise HTTPException(404,"Document not found")
    return run(d.content,req.target_language)
