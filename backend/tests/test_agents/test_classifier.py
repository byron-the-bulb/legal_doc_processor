from app.agents.document_classifier import DocumentClassificationAgent

def test_classifier_detects_keywords():
    agent = DocumentClassificationAgent()
    res = agent.classify("Scheduling Order: hearing set for 01/10/2026")
    assert res.document_type in ("court_order", "unknown")
    assert 0.0 <= res.confidence_score <= 1.0
