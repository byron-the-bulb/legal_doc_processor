from __future__ import annotations
from typing import List, Tuple

from app.models.schemas import ExtractedDate, LegalObligation
from .base_parser import BaseParser


class PoliceParser(BaseParser):
    name = "police"

    def parse(self, text: str) -> Tuple[List[ExtractedDate], List[LegalObligation]]:
        dates: List[ExtractedDate] = []
        obligations: List[LegalObligation] = []
        lower = text.lower()
        for dt in self._find_dates(text):
            dtype = "incident_date" if any(k in lower for k in ["incident", "collision", "accident"]) else "date"
            dates.append(
                ExtractedDate(
                    date=dt,
                    date_type=dtype,
                    confidence_score=0.6,
                    source_text="police parser heuristic",
                    jurisdiction=None,
                )
            )
        if any(k in lower for k in ["police report", "officer", "case number", "citation"]):
            # Usually review, obtain or authenticate police report
            if dates:
                obligations.append(
                    LegalObligation(
                        description="Review police report and confirm incident details",
                        due_date=dates[0].date,
                        responsible_party="Paralegal",
                        priority_level="medium",
                        associated_case="",
                        source_document="police_report",
                    )
                )
        return dates, obligations
