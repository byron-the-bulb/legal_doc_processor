from __future__ import annotations
import os
import base64
import logging
from typing import List, Optional

try:
    from pydantic_ai import Agent  # type: ignore
except Exception:  # pragma: no cover
    Agent = object  # fallback for scaffolding

from app.models.schemas import DocumentClassification
from app.core.config import settings

ALLOWED_TYPES = [
    "court_order",
    "insurance_correspondence",
    "medical_records",
    "settlement_communication",
    "discovery_request",
    "employment_records",
    "expert_witness_report",
    "police_report",
    "unknown",
]

# Logger
logger = logging.getLogger(__name__)
# Allow env override: DOC_CLS_LOG_LEVEL or LOG_LEVEL
_lvl_name = os.getenv("DOC_CLS_LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO")).upper()
logger.setLevel(getattr(logging, _lvl_name, logging.INFO))
# Ensure logs are visible even if app hasn't configured logging
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_handler)


def _unknown_for_escalation() -> DocumentClassification:
    logger.info("Classifier: LLM unavailable/failed -> returning unknown to trigger escalation")
    return DocumentClassification(
        document_type="unknown",
        confidence_score=0.0,
        sub_type=None,
        jurisdiction=None,
        parties_involved=[],
    )


def _encode_images_as_data_urls(image_paths: List[str], max_images: int = 2) -> List[str]:
    data_urls: List[str] = []
    for p in image_paths[:max_images]:
        try:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            # best-effort mime guessing
            ext = os.path.splitext(p)[1].lower().strip(".")
            mime = {
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "webp": "image/webp",
                "tif": "image/tiff",
                "tiff": "image/tiff",
                "bmp": "image/bmp",
            }.get(ext, "image/png")
            data_urls.append(f"data:{mime};base64,{b64}")
        except Exception:
            # skip unreadable images
            continue
    return data_urls


class DocumentClassificationAgent(Agent):
    """LLM-backed document classification (escalates on failure, no heuristics).

    classify(text, images) -> DocumentClassification
    - text: extracted text from the document (OCR, PDF, DOCX, etc.)
    - images: optional list of file paths for page images to give the LLM visual context (first N used)
    """

    def __init__(self) -> None:  # type: ignore[no-untyped-def]
        # Lazy import to avoid hard dependency if not used
        self._openai_client = None
        try:
            from openai import OpenAI  # type: ignore

            # Prefer settings (loads from .env) and fall back to real env
            api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            model = settings.OPENAI_MODEL or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            if api_key:
                self._openai_client = OpenAI(api_key=api_key)
                logger.info(
                    "DocumentClassifier initialized with OpenAI client | model=%s | api_key_source=%s",
                    model,
                    ("settings" if settings.OPENAI_API_KEY else "env"),
                )
            else:
                logger.info("DocumentClassifier: no OPENAI_API_KEY; classification will escalate on use")
        except Exception as e:
            self._openai_client = None
            logger.warning("DocumentClassifier: failed to initialize OpenAI client; classification will escalate on use | error=%r", e)

    def classify(self, text: str, images: Optional[List[str]] = None) -> DocumentClassification:
        # If no client or no API key, return unknown to escalate
        if not self._openai_client:
            logger.info("Classifier: no OpenAI client (no API key?) -> escalate")
            return _unknown_for_escalation()

        # Build multimodal prompt; keep within reasonable token budget
        truncated_text = (text or "")[:12000]
        data_urls = _encode_images_as_data_urls(images or []) if images else []
        model = settings.OPENAI_MODEL or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(
            "Classifier branch: LLM | model=%s | text_len=%d | images=%d",
            model,
            len(truncated_text),
            len(data_urls),
        )

        system_prompt = (
            "You are a legal document classification agent for a personal injury law firm. "
            "Classify the document into one of the allowed types and extract metadata. "
            "Allowed types strictly limited to: " + ", ".join(ALLOWED_TYPES) + ". "
            "Respond ONLY with a compact JSON object with keys: "
            "document_type (one of allowed), confidence_score (0..1), sub_type (string or null), "
            "jurisdiction (string or null), parties_involved (array of strings)."
        )

        # Compose user content with text and optional images
        user_parts: List[dict] = [
            {"type": "text", "text": (
                "Task: Determine the document type and extract metadata.\n\n"
                "Use both the extracted text and any provided page images.\n\n"
                "Extracted text (may be partial):\n" + truncated_text
            )}
        ]
        for url in data_urls:
            user_parts.append({"type": "image_url", "image_url": {"url": url}})

        # Call OpenAI chat with a JSON-structured answer instruction
        try:
            # Prefer a small multimodal model if available
            completion = self._openai_client.chat.completions.create(  # type: ignore[attr-defined]
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_parts},
                ],
            )
            content = completion.choices[0].message.content or "{}"
            logger.debug("LLM raw response length=%d", len(content))
            logger.debug("LLM raw response: %s", content)
        except Exception as e:
            logger.warning("Classifier: LLM call failed -> escalate | error=%r", e)
            return DocumentClassification(
                document_type="unknown",
                confidence_score=0.0,
                sub_type=None,
                jurisdiction=None,
                parties_involved=[],
            )

        # Parse JSON response
        import json

        try:
            data = json.loads(content)
            # sanitize
            dtype = data.get("document_type", "unknown")
            if dtype not in ALLOWED_TYPES:
                dtype = "unknown"
            conf = data.get("confidence_score", 0.0)
            try:
                conf = float(conf)
            except Exception:
                conf = 0.0
            conf = max(0.0, min(1.0, conf))
            sub_type = data.get("sub_type")
            jurisdiction = data.get("jurisdiction")
            parties = data.get("parties_involved") or []
            if not isinstance(parties, list):
                parties = []
            parties = [str(p) for p in parties][:10]
            logger.info("Classification result: type=%s | confidence=%.2f", dtype, conf)
            return DocumentClassification(
                document_type=dtype,
                confidence_score=conf,
                sub_type=sub_type,
                jurisdiction=jurisdiction,
                parties_involved=parties,
            )
        except Exception as e:
            # Any parsing failure -> escalate
            logger.warning("Classifier: LLM JSON parse failed -> escalate | error=%r", e)
            return _unknown_for_escalation()
