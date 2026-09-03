import logging
from fastapi import APIRouter,UploadFile,File,Depends,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.db.session import get_db
from app.db.models.document import Document
from app.services.document_service import process_upload

logger = logging.getLogger(__name__)
router=APIRouter(prefix="/documents",tags=["documents"])
@router.post("/upload")
def upload(file:UploadFile=File(...),db:Session=Depends(get_db)):
    if not file.filename: raise HTTPException(400,"Missing filename")
    try:
        text,doc_type=process_upload(file)
    except Exception as e:
        logger.exception(f"process_upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {e}")
    if not text or not text.strip(): raise HTTPException(422,"No readable text found")
    try:
        doc=Document(filename=file.filename,content=text,doc_type=doc_type); db.add(doc);db.commit();db.refresh(doc)
    except OperationalError as e:
        logger.exception(f"DB OperationalError on upload: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e.orig if hasattr(e,'orig') else e}. Check DATABASE_URL on Vercel.")
    except SQLAlchemyError as e:
        logger.exception(f"DB error on upload: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error on upload: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    return {"id":doc.id,"filename":doc.filename,"document_type":doc.doc_type,"characters":len(text)}
@router.get("/{document_id}")
def get_document(document_id:int,db:Session=Depends(get_db)):
    d=db.get(Document,document_id)
    if not d: raise HTTPException(404,"Document not found")
    return {"id":d.id,"filename":d.filename,"content":d.content,"document_type":d.doc_type}
