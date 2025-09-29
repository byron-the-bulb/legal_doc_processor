import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import settings
from app.models import schemas
from app.models.database import Document, CalendarEvent
from app.services.document_processor import process_document_task

router = APIRouter()


@router.post("/documents/upload", response_model=schemas.ProcessingResult)
async def upload_document(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    doc_id = str(uuid.uuid4())
    dest_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{file.filename}")
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create DB record
    db_doc = Document(
        id=doc_id,
        filename=file.filename,
        path=dest_path,
        case_id=case_id,
        status="queued",
    )
    db.add(db_doc)
    db.commit()

    # Kick off async processing
    process_document_task.delay(doc_id)

    return schemas.ProcessingResult(
        document_id=doc_id,
        classification=schemas.DocumentClassification(
            document_type="unknown", confidence_score=0.0, sub_type=None, jurisdiction=None, parties_involved=[]
        ),
        extracted_dates=[],
        obligations=[],
        processing_status="queued",
        human_review_required=False,
        error_messages=[],
    )


@router.get("/documents/{document_id}/status", response_model=dict)
async def get_status(document_id: str, db: Session = Depends(get_db)):
    db_doc = db.get(Document, document_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document_id": document_id, "status": db_doc.status}


@router.get("/documents/{document_id}/result", response_model=schemas.ProcessingResult)
async def get_result(document_id: str, db: Session = Depends(get_db)):
    db_doc = db.get(Document, document_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if db_doc.status not in ("completed", "needs_review", "failed"):
        raise HTTPException(status_code=202, detail="Processing not completed")

    return schemas.ProcessingResult(
        document_id=db_doc.id,
        classification=db_doc.classification or schemas.DocumentClassification(
            document_type="unknown", confidence_score=0.0, sub_type=None, jurisdiction=None, parties_involved=[]
        ),
        extracted_dates=db_doc.extracted_dates or [],
        obligations=db_doc.obligations or [],
        processing_status=db_doc.status,
        human_review_required=db_doc.human_review_required or False,
        error_messages=db_doc.error_messages or [],
    )


@router.get("/cases/{case_id}/calendar", response_model=List[schemas.CalendarEventOut])
async def get_case_calendar(case_id: str, db: Session = Depends(get_db)):
    events = db.query(CalendarEvent).filter(CalendarEvent.case_id == case_id).order_by(CalendarEvent.start.asc()).all()
    return [schemas.CalendarEventOut.from_orm(e) for e in events]


@router.post("/cases/{case_id}/calendar/events", response_model=schemas.CalendarEventOut)
async def create_calendar_event(case_id: str, event: schemas.CalendarEventCreate, db: Session = Depends(get_db)):
    db_event = CalendarEvent(
        id=str(uuid.uuid4()),
        case_id=case_id,
        title=event.title,
        description=event.description,
        start=event.start,
        end=event.end,
        all_day=event.all_day,
        source_document=event.source_document,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return schemas.CalendarEventOut.from_orm(db_event)


@router.get("/documents", response_model=List[schemas.DocumentListItem])
async def list_documents(
    case_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(Document)
    if case_id:
        q = q.filter(Document.case_id == case_id)
    q = q.order_by(Document.created_at.desc()).offset(max(0, offset)).limit(max(1, min(limit, 200)))
    rows = q.all()
    out: List[schemas.DocumentListItem] = []
    for r in rows:
        out.append(
            schemas.DocumentListItem(
                document_id=r.id,
                filename=r.filename,
                case_id=r.case_id,
                created_at=r.created_at,
                processing_status=r.status,
                classification=(
                    r.classification
                    or schemas.DocumentClassification(
                        document_type="unknown",
                        confidence_score=0.0,
                        sub_type=None,
                        jurisdiction=None,
                        parties_involved=[],
                    )
                ),
                extracted_dates=r.extracted_dates or [],
                obligations=r.obligations or [],
                human_review_required=bool(r.human_review_required),
                error_messages=r.error_messages or [],
            )
        )
    return out
