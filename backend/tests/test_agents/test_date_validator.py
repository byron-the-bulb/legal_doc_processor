from datetime import datetime
from app.agents.date_validator import DateValidationAgent
from app.models.schemas import ExtractedDate


def test_date_validator_basic():
    agent = DateValidationAgent()
    d = ExtractedDate(date=datetime.utcnow(), date_type="deadline", confidence_score=1.0, source_text="x", jurisdiction=None)
    valid, warnings = agent.validate([d])
    assert len(valid) == 1
    assert isinstance(warnings, list)
