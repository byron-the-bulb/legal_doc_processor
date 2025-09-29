from __future__ import annotations
from datetime import datetime, timedelta
from typing import List

from app.models.schemas import DocumentClassification, LegalObligation


class ObligationExtractorAgent:
    KEY_PHRASES = [
         ("file response", 30, "Attorney"),
         ("respond within", 30, "Attorney"),
         ("produce documents", 14, "Paralegal"),
         ("attend mediation", 0, "Attorney"),
    ]

    def extract(self, text: str, classification: DocumentClassification) -> List[LegalObligation]:
        lower = text.lower()
        obligations: List[LegalObligation] = []
        now = datetime.utcnow()
        for phrase, days, owner in self.KEY_PHRASES:
            if phrase in lower:
                obligations.append(
                    LegalObligation(
                        description=phrase.title(),
                        due_date=now + timedelta(days=days),
                        responsible_party=owner,
                        priority_level="high" if days <= 10 else "medium",
                        associated_case="",
                        source_document=classification.document_type,
                    )
                )
        return obligations
