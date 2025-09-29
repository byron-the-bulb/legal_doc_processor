from __future__ import annotations
from typing import List, Tuple

from app.models.schemas import DocumentClassification, ExtractedDate, LegalObligation


class HumanEscalationAgent:
    """Decides whether the case needs human review and crafts review prompts."""

    def evaluate(
        self,
        classification: DocumentClassification,
        dates: List[ExtractedDate],
        obligations: List[LegalObligation],
        warnings: List[str],
    ) -> Tuple[bool, List[str]]:
        msgs: List[str] = []
        needs = False

        if classification.confidence_score < 0.5:
            needs = True
            msgs.append("Low classification confidence. Please confirm document type.")

        if not dates and not obligations:
            needs = True
            msgs.append("No dates or obligations extracted. Provide key dates and tasks, if any.")

        if warnings:
            needs = True
            msgs.extend([f"Validator warning: {w}" for w in warnings])

        # Ask specific questions to guide review
        if needs:
            msgs.append("Are there explicit deadlines (e.g., 'within 30 days') or scheduled events?")
            msgs.append("Identify responsible party for each task (Attorney or Paralegal).")

        return needs, msgs
