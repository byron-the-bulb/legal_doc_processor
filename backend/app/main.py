import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.models.database import Base, engine
from app.core.config import settings

app = FastAPI(title="Legal Document Processor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    # Ensure storage directories exist
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    # Create tables once database is reachable
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

app.include_router(api_router, prefix="/api/v1")
