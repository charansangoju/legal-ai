from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from app.services.speech_service import info, process_stt, process_tts

router = APIRouter(prefix="/speech", tags=["speech"])

class TTSRequest(BaseModel):
    text: str
    language: str = "en"

@router.get("/status")
def status():
    return info()

@router.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    contents = await file.read()
    return process_stt(contents, file.filename or "recording.wav")

@router.post("/tts")
def text_to_speech(req: TTSRequest):
    return process_tts(req.text, req.language)
