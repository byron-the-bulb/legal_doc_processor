from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session

from app.models.schemas import ExtractedDate
from app.services.calendar_service import add_calendar_entries, detect_conflicts


class CalendarIntegrationAgent:
    """Integrates validated dates into the case calendar and checks for conflicts."""

    def integrate(self, db: Session, case_id: str | None, dates: List[ExtractedDate]) -> List[str]:
        if not case_id:
            # Without a case context we cannot write calendar entries
            return []
        add_calendar_entries(db, case_id, dates)
        conflicts = detect_conflicts(db, case_id, dates)
        return conflicts
