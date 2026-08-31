from fastapi import APIRouter,UploadFile,File,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.document import Document
from app.services.document_service import process_upload
router=APIRouter(prefix="/documents",tags=["documents"])
@router.post("/upload")
def upload(file:UploadFile=File(...),db:Session=Depends(get_db)):
    if not file.filename: raise HTTPException(400,"Missing filename")
    text,doc_type=process_upload(file)
    if not text: raise HTTPException(422,"No readable text found")
    doc=Document(filename=file.filename,content=text,doc_type=doc_type); db.add(doc);db.commit();db.refresh(doc)
    return {"id":doc.id,"filename":doc.filename,"document_type":doc.doc_type,"characters":len(text)}
@router.get("/{document_id}")
def get_document(document_id:int,db:Session=Depends(get_db)):
    d=db.get(Document,document_id)
    if not d: raise HTTPException(404,"Document not found")
    return {"id":d.id,"filename":d.filename,"content":d.content,"document_type":d.doc_type}
