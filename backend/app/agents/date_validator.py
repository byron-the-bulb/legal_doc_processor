from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Tuple
from dateutil.relativedelta import relativedelta

from app.models.schemas import ExtractedDate


class DateValidationAgent:
    def validate(self, dates: List[ExtractedDate]) -> Tuple[List[ExtractedDate], List[str]]:
        valid = []
        warnings = []
        now = datetime.utcnow()
        for d in dates:
            if d.date.year < 1990 or d.date.year > now.year + 5:
                warnings.append(f"Suspicious date detected: {d.date}")
                continue
            valid.append(d)
        # Placeholder for court rule calculations; e.g., add 30-day deadlines after service
        # In a real implementation, we'd use jurisdiction-specific rules.
        return valid, warnings
