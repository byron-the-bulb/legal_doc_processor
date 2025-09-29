from __future__ import annotations
from typing import List, Tuple

from app.models.schemas import ExtractedDate, LegalObligation
from .base_parser import BaseParser


class MedicalParser(BaseParser):
    name = "medical"

    def parse(self, text: str) -> Tuple[List[ExtractedDate], List[LegalObligation]]:
        dates = []
        obligations = []
        lower = text.lower()
        for dt in self._find_dates(text):
            dtype = "appointment" if any(w in lower for w in ["appointment", "visit"]) else "treatment"
            dates.append(
                ExtractedDate(
                    date=dt,
                    date_type=dtype,
                    confidence_score=0.6,
                    source_text="medical parser heuristic",
                    jurisdiction=None,
                )
            )
        if ("mmi" in lower or "maximum medical improvement" in lower) and dates:
            # add a placeholder obligation
            obligations.append(
                LegalObligation(
                    description="Review MMI status",
                    due_date=dates[0].date,
                    responsible_party="Attorney",
                    priority_level="medium",
                    associated_case="",
                    source_document="medical",
                )
            )
        return dates, obligations
