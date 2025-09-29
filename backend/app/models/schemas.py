from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
try:
    # pydantic v2
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    ConfigDict = dict  # type: ignore


class ExtractedDate(BaseModel):
    date: datetime
    date_type: str  # "deadline", "hearing", "appointment", etc.
    confidence_score: float
    source_text: str
    jurisdiction: Optional[str]


class LegalObligation(BaseModel):
    description: str
    due_date: datetime
    responsible_party: str
    priority_level: str
    associated_case: str
    source_document: str


class DocumentClassification(BaseModel):
    document_type: str
    confidence_score: float
    sub_type: Optional[str]
    jurisdiction: Optional[str]
    parties_involved: List[str] = []


class ProcessingResult(BaseModel):
    document_id: str
    classification: DocumentClassification
    extracted_dates: List[ExtractedDate]
    obligations: List[LegalObligation]
    processing_status: str
    human_review_required: bool
    error_messages: List[str]


# Extra schemas for API I/O
class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start: datetime
    end: datetime
    all_day: bool = False
    source_document: Optional[str] = None


class CalendarEventOut(BaseModel):
    id: str
    case_id: str
    title: str
    description: Optional[str]
    start: datetime
    end: datetime
    all_day: bool
    source_document: Optional[str]

    # Pydantic v2 style config for ORM support
    model_config = ConfigDict(from_attributes=True)  # type: ignore


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    case_id: Optional[str]
    created_at: datetime
    processing_status: str
    classification: DocumentClassification
    extracted_dates: List[ExtractedDate]
    obligations: List[LegalObligation]
    human_review_required: bool
    error_messages: List[str]
