from __future__ import annotations
from typing import List, Tuple

from app.models.schemas import ExtractedDate, LegalObligation
from .base_parser import BaseParser


class EmploymentParser(BaseParser):
    name = "employment"

    def parse(self, text: str) -> Tuple[List[ExtractedDate], List[LegalObligation]]:
        dates: List[ExtractedDate] = []
        obligations: List[LegalObligation] = []
        lower = text.lower()
        for dt in self._find_dates(text):
            dtype = "work_date" if any(k in lower for k in ["worked", "shift", "timecard"]) else "deadline"
            dates.append(
                ExtractedDate(
                    date=dt,
                    date_type=dtype,
                    confidence_score=0.6,
                    source_text="employment parser heuristic",
                    jurisdiction=None,
                )
            )
        if ("return to work" in lower or "rtw" in lower) and dates:
            obligations.append(
                LegalObligation(
                    description="Confirm return-to-work date",
                    due_date=dates[0].date,
                    responsible_party="Paralegal",
                    priority_level="medium",
                    associated_case="",
                    source_document="employment",
                )
            )
        return dates, obligations
