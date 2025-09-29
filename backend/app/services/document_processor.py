from __future__ import annotations
import io
import json
from datetime import datetime
from typing import List, Tuple
import os
import tempfile

import logging
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.services.celery_app import celery_app
from app.core.config import settings
from app.models.database import SessionLocal, Document
from app.models.schemas import (
    DocumentClassification,
    ExtractedDate,
    LegalObligation,
)
from app.agents.document_classifier import DocumentClassificationAgent
from app.agents.parsers.court_parser import CourtParser
from app.agents.parsers.insurance_parser import InsuranceParser
from app.agents.parsers.medical_parser import MedicalParser
from app.agents.parsers.settlement_parser import SettlementParser
from app.agents.parsers.discovery_parser import DiscoveryParser
from app.agents.parsers.employment_parser import EmploymentParser
from app.agents.parsers.expert_parser import ExpertParser
from app.agents.parsers.police_parser import PoliceParser
from app.agents.date_validator import DateValidationAgent
from app.agents.obligation_extractor import ObligationExtractorAgent
from app.agents.calendar_integrator import CalendarIntegrationAgent
from app.agents.human_escalation import HumanEscalationAgent

import pytesseract
from PIL import Image
import PyPDF2
import docx

logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_h)
_lvl_name = os.getenv("PIPELINE_LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO")).upper()
logger.setLevel(getattr(logging, _lvl_name, logging.INFO))


def _extract_text_from_pdf(path: str) -> str:
    try:
        texts = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                txt = page.extract_text() or ""
                texts.append(txt)
        return "\n".join(texts)
    except Exception:
        return ""


def _extract_text_from_docx(path: str) -> str:
    try:
        d = docx.Document(path)
        return "\n".join([p.text for p in d.paragraphs])
    except Exception:
        return ""


def _extract_text_from_image(path: str) -> str:
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img)
    except Exception:
        return ""


def extract_text(path: str) -> str:
    path_l = path.lower()
    if path_l.endswith(".pdf"):
        return _extract_text_from_pdf(path)
    if path_l.endswith(".docx"):
        return _extract_text_from_docx(path)
    if any(path_l.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]):
        return _extract_text_from_image(path)
    # fallback
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _render_pdf_preview_images(path: str, max_pages: int = 2) -> List[str]:
    """Render up to max_pages of a PDF to PNG images and return file paths. Best-effort.
    Requires poppler for pdf2image; logs and returns [] on failure.
    """
    try:
        from pdf2image import convert_from_path  # type: ignore
    except Exception as e:
        logger.info("pdf2image not available; skipping PDF image previews: %r", e)
        return []

    out_paths: List[str] = []
    try:
        tmp_dir = tempfile.mkdtemp(prefix="pdf_preview_", dir=settings.STORAGE_DIR)
    except Exception:
        tmp_dir = tempfile.mkdtemp(prefix="pdf_preview_")
    try:
        poppler_path = settings.POPPLER_PATH
        logger.info(
            "PDF preview: rendering | file=%s | max_pages=%d | poppler_path=%s",
            path,
            max_pages,
            poppler_path or "(default)",
        )
        kwargs = dict(first_page=1, last_page=max_pages)
        if poppler_path:
            kwargs["poppler_path"] = poppler_path
        images = convert_from_path(path, **kwargs)
        for idx, img in enumerate(images, start=1):
            out_path = os.path.join(tmp_dir, f"page_{idx}.png")
            img.save(out_path, format="PNG")
            out_paths.append(out_path)
        logger.info("PDF preview: rendered %d image(s) at %s", len(out_paths), tmp_dir)
    except Exception as e:
        logger.info("PDF preview: rendering failed; continuing without images: %r", e)
    return out_paths


@celery_app.task(name="process_document_task")
def process_document_task(document_id: str) -> None:
    db: Session = SessionLocal()
    preview_paths: List[str] = []
    try:
        doc: Document = db.get(Document, document_id)
        if not doc:
            logger.error("Document not found: %s", document_id)
            return
        doc.status = "processing"
        db.commit()

        # Extract text
        text = extract_text(doc.path)
        # For PDFs, also render first pages to images
        if doc.path.lower().endswith(".pdf"):
            logger.info("Pipeline: PDF detected | doc_id=%s | path=%s", document_id, doc.path)
            preview_paths = _render_pdf_preview_images(doc.path, max_pages=2)
        else:
            logger.info("Pipeline: non-PDF document | doc_id=%s | path=%s", document_id, doc.path)

        # Agents pipeline
        classifier = DocumentClassificationAgent()
        classification = classifier.classify(text, images=preview_paths or None)
        logger.info(
            "Pipeline: classification | doc_id=%s | type=%s | confidence=%.2f | images=%d",
            document_id,
            getattr(classification, "document_type", "unknown"),
            float(getattr(classification, "confidence_score", 0.0) or 0.0),
            len(preview_paths),
        )

        parser_dates: List[ExtractedDate] = []
        obligations: List[LegalObligation] = []

        if classification.document_type == "court_order":
            logger.info(
                "Pipeline: invoking parser | doc_id=%s | parser=CourtParser | images=%d",
                document_id,
                len(preview_paths),
            )
            dates, obs = CourtParser().parse(text, images=preview_paths or None)
            logger.info(
                "Pipeline: parser result | parser=CourtParser | dates=%d | obligations=%d",
                len(dates),
                len(obs),
            )
        elif classification.document_type == "insurance_correspondence":
            logger.info("Pipeline: invoking parser | doc_id=%s | parser=InsuranceParser", document_id)
            dates, obs = InsuranceParser().parse(text)
            logger.info("Pipeline: parser result | parser=InsuranceParser | dates=%d | obligations=%d", len(dates), len(obs))
        elif classification.document_type == "medical_records":
            logger.info("Pipeline: invoking parser | doc_id=%s | parser=MedicalParser", document_id)
            dates, obs = MedicalParser().parse(text)
            logger.info("Pipeline: parser result | parser=MedicalParser | dates=%d | obligations=%d", len(dates), len(obs))
        elif classification.document_type == "settlement_communication":
            logger.info("Pipeline: invoking parser | doc_id=%s | parser=SettlementParser", document_id)
            dates, obs = SettlementParser().parse(text)
            logger.info("Pipeline: parser result | parser=SettlementParser | dates=%d | obligations=%d", len(dates), len(obs))
        elif classification.document_type == "discovery_request":
            logger.info("Pipeline: invoking parser | doc_id=%s | parser=DiscoveryParser", document_id)
            dates, obs = DiscoveryParser().parse(text)
            logger.info("Pipeline: parser result | parser=DiscoveryParser | dates=%d | obligations=%d", len(dates), len(obs))
        elif classification.document_type == "employment_records":
            logger.info("Pipeline: invoking parser | doc_id=%s | parser=EmploymentParser", document_id)
            dates, obs = EmploymentParser().parse(text)
            logger.info("Pipeline: parser result | parser=EmploymentParser | dates=%d | obligations=%d", len(dates), len(obs))
        elif classification.document_type == "expert_witness_report":
            logger.info("Pipeline: invoking parser | doc_id=%s | parser=ExpertParser", document_id)
            dates, obs = ExpertParser().parse(text)
            logger.info("Pipeline: parser result | parser=ExpertParser | dates=%d | obligations=%d", len(dates), len(obs))
        elif classification.document_type == "police_report":
            logger.info("Pipeline: invoking parser | doc_id=%s | parser=PoliceParser", document_id)
            dates, obs = PoliceParser().parse(text)
            logger.info("Pipeline: parser result | parser=PoliceParser | dates=%d | obligations=%d", len(dates), len(obs))
        else:
            # Unknown or unsupported classification: escalate (no parser run)
            logger.info(
                "Pipeline: classification unsupported/unknown -> skipping parsers to trigger escalation | doc_id=%s",
                document_id,
            )
            dates, obs = [], []

        validator = DateValidationAgent()
        valid_dates, warnings = validator.validate(dates)

        obligation_agent = ObligationExtractorAgent()
        extracted_obligations = obligation_agent.extract(text, classification)
        obligations = obs + extracted_obligations

        calendar_agent = CalendarIntegrationAgent()
        calendar_agent.integrate(db, doc.case_id, valid_dates)

        # decide if human review is needed
        human_agent = HumanEscalationAgent()
        needs_review, review_msgs = human_agent.evaluate(classification, valid_dates, obligations, warnings)

        # Persist results
        doc.classification = jsonable_encoder(classification)
        doc.extracted_dates = jsonable_encoder(valid_dates)
        doc.obligations = jsonable_encoder(obligations)
        doc.human_review_required = needs_review
        doc.error_messages = review_msgs
        doc.status = "needs_review" if needs_review else "completed"
        db.commit()
    except Exception as e:
        logger.exception("Processing failed: %s", e)
        try:
            doc = db.get(Document, document_id)
            if doc:
                doc.status = "failed"
                doc.error_messages = [str(e)]
                db.commit()
        except Exception:  # pragma: no cover
            pass
    finally:
        db.close()
        # cleanup preview images
        for p in preview_paths:
            try:
                os.remove(p)
            except Exception:
                pass
