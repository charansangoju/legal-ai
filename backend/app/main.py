from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()
from app.db.session import Base,engine
from app.db.models import document,analysis,translation,conversation
from app.api.v1 import documents,analysis as analysis_api,chat,auth,translation as translation_api,summarization,speech
Base.metadata.create_all(bind=engine)
app=FastAPI(title="Legal AI API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
for r in [documents.router,analysis_api.router,chat.router,auth.router,translation_api.router,summarization.router,speech.router]: app.include_router(r,prefix="/api/v1")
@app.get("/health")
def health(): return {"status":"ok","service":"legal-ai"}
