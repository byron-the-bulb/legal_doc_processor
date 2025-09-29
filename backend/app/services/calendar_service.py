from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from app.models.schemas import ExtractedDate, LegalObligation
from app.models.database import CalendarEvent


def add_calendar_entries(db: Session, case_id: str, dates: List[ExtractedDate]) -> None:
    for d in dates:
        title = f"{d.date_type.title()}"
        event = CalendarEvent(
            id=f"evt-{case_id}-{d.date.timestamp()}",
            case_id=case_id,
            title=title,
            description=d.source_text,
            start=d.date,
            end=d.date,
            all_day=True,
            source_document="auto",
        )
        db.merge(event)
    db.commit()


def detect_conflicts(db: Session, case_id: str, new_dates: List[ExtractedDate]) -> List[str]:
    conflicts = []
    existing = db.query(CalendarEvent).filter(CalendarEvent.case_id == case_id).all()
    for nd in new_dates:
        for ev in existing:
            if abs((ev.start - nd.date).total_seconds()) < 60 * 60:  # 1 hour proximity
                conflicts.append(f"Potential conflict: {nd.date_type} near existing event '{ev.title}' at {ev.start}")
    return conflicts
