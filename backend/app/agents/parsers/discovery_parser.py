from __future__ import annotations
from typing import List, Tuple

from app.models.schemas import ExtractedDate, LegalObligation
from .base_parser import BaseParser


class DiscoveryParser(BaseParser):
    name = "discovery"

    def parse(self, text: str) -> Tuple[List[ExtractedDate], List[LegalObligation]]:
        dates: List[ExtractedDate] = []
        obligations: List[LegalObligation] = []
        lower = text.lower()
        for dt in self._find_dates(text):
            dtype = "deposition" if "deposition" in lower else "production_deadline"
            dates.append(
                ExtractedDate(
                    date=dt,
                    date_type=dtype,
                    confidence_score=0.6,
                    source_text="discovery parser heuristic",
                    jurisdiction=None,
                )
            )
        if any(k in lower for k in ["interrogatories", "requests for production", "admissions"]) and dates:
            obligations.append(
                LegalObligation(
                    description="Respond to discovery",
                    due_date=dates[0].date,
                    responsible_party="Attorney",
                    priority_level="high",
                    associated_case="",
                    source_document="discovery",
                )
            )
        return dates, obligations
