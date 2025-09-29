from __future__ import annotations
from typing import List, Tuple

from app.models.schemas import ExtractedDate, LegalObligation
from .base_parser import BaseParser


class InsuranceParser(BaseParser):
    name = "insurance"

    def parse(self, text: str) -> Tuple[List[ExtractedDate], List[LegalObligation]]:
        dates = []
        obligations = []
        lower = text.lower()
        for dt in self._find_dates(text):
            dtype = "deadline" if "respond" in lower or "response" in lower else "coverage_date"
            dates.append(
                ExtractedDate(
                    date=dt,
                    date_type=dtype,
                    confidence_score=0.6,
                    source_text="insurance parser heuristic",
                    jurisdiction=None,
                )
            )
        if "policy" in lower and "limit" in lower and dates:
            obligations.append(
                LegalObligation(
                    description="Confirm policy limits",
                    due_date=dates[0].date,
                    responsible_party="Paralegal",
                    priority_level="medium",
                    associated_case="",
                    source_document="insurance",
                )
            )
        return dates, obligations
