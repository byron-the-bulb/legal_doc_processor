from __future__ import annotations
from typing import List, Tuple

from app.models.schemas import ExtractedDate, LegalObligation
from .base_parser import BaseParser


class SettlementParser(BaseParser):
    name = "settlement"

    def parse(self, text: str) -> Tuple[List[ExtractedDate], List[LegalObligation]]:
        dates: List[ExtractedDate] = []
        obligations: List[LegalObligation] = []
        lower = text.lower()
        for dt in self._find_dates(text):
            dtype = "mediation" if "mediation" in lower else "deadline"
            dates.append(
                ExtractedDate(
                    date=dt,
                    date_type=dtype,
                    confidence_score=0.6,
                    source_text="settlement parser heuristic",
                    jurisdiction=None,
                )
            )
        if ("offer" in lower or "demand" in lower) and dates:
            obligations.append(
                LegalObligation(
                    description="Evaluate settlement offer",
                    due_date=dates[0].date,
                    responsible_party="Attorney",
                    priority_level="high",
                    associated_case="",
                    source_document="settlement",
                )
            )
        return dates, obligations
