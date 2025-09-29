from __future__ import annotations
from typing import List, Tuple

from app.models.schemas import ExtractedDate, LegalObligation
from .base_parser import BaseParser


class ExpertParser(BaseParser):
    name = "expert"

    def parse(self, text: str) -> Tuple[List[ExtractedDate], List[LegalObligation]]:
        dates: List[ExtractedDate] = []
        obligations: List[LegalObligation] = []
        lower = text.lower()
        for dt in self._find_dates(text):
            dtype = "report_deadline" if any(k in lower for k in ["report", "disclosure"]) else "deadline"
            dates.append(
                ExtractedDate(
                    date=dt,
                    date_type=dtype,
                    confidence_score=0.6,
                    source_text="expert parser heuristic",
                    jurisdiction=None,
                )
            )
        if any(k in lower for k in ["expert", "witness"]) and dates:
            obligations.append(
                LegalObligation(
                    description="Serve expert disclosures",
                    due_date=dates[0].date,
                    responsible_party="Attorney",
                    priority_level="high",
                    associated_case="",
                    source_document="expert_witness_report",
                )
            )
        return dates, obligations
