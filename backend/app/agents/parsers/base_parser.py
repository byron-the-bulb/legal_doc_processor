from __future__ import annotations
import os
import re
import json
import base64
import logging
from datetime import datetime
from dateutil import parser as dateparser
from typing import List, Tuple, Optional

from app.models.schemas import ExtractedDate, LegalObligation
from app.core.config import settings


logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_h)
_lvl_name = os.getenv("PARSER_LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO")).upper()
logger.setLevel(getattr(logging, _lvl_name, logging.INFO))


def _encode_images_as_data_urls(image_paths: List[str], max_images: int = 2) -> List[str]:
    data_urls: List[str] = []
    for p in image_paths[:max_images]:
        try:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
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
            continue
    return data_urls


class BaseParser:
    name = "base"

    def parse(self, text: str, images: Optional[List[str]] = None) -> Tuple[List[ExtractedDate], List[LegalObligation]]:
        # LLM-first generic extraction
        try:
            image_urls = _encode_images_as_data_urls(images or []) if images else []
            system_prompt = (
                "You are a legal document parsing agent. Using the extracted text and any provided page images, "
                "extract key dates and obligations from any legal document.\n\n"
                "Return ONLY JSON with fields: \n"
                "- dates: array of {date_iso (ISO8601), date_type (string), source_text}\n"
                "- obligations: array of {description, due_date_iso (ISO8601), responsible_party, priority_level}\n\n"
                "Rules: \n"
                "- Only include an obligation if a due_date is explicitly present; otherwise omit it.\n"
                "- Keep types concise (e.g., hearing, trial, deposition, deadline, mediation, appointment).\n"
                "- Do not hallucinate. If not sure, leave arrays empty.\n"
            )
            user_parts: List[dict] = [
                {"type": "text", "text": (
                    "Task: Extract dates and obligations, if present.\n\n"
                    "Extracted text (may be partial):\n" + (text or "")[:12000]
                )}
            ]
            for url in image_urls:
                user_parts.append({"type": "image_url", "image_url": {"url": url}})

            data = self._llm_json(system_prompt, user_parts)
            if data is not None:
                out_dates: List[ExtractedDate] = []
                out_obs: List[LegalObligation] = []
                for d in data.get("dates", []) or []:
                    try:
                        when = dateparser.parse(str(d.get("date_iso")), fuzzy=True)
                        dtype = str(d.get("date_type") or "deadline")
                        out_dates.append(
                            ExtractedDate(
                                date=when,
                                date_type=dtype,
                                confidence_score=0.7,
                                source_text=str(d.get("source_text") or "base parser llm"),
                                jurisdiction=None,
                            )
                        )
                    except Exception:
                        continue
                for o in data.get("obligations", []) or []:
                    try:
                        due = dateparser.parse(str(o.get("due_date_iso")), fuzzy=True)
                    except Exception:
                        continue
                    desc = str(o.get("description") or "")
                    if not desc:
                        continue
                    out_obs.append(
                        LegalObligation(
                            description=desc,
                            due_date=due,
                            responsible_party=str(o.get("responsible_party") or "Attorney"),
                            priority_level=str(o.get("priority_level") or "medium"),
                            associated_case="",
                            source_document=self.name,
                        )
                    )
                logger.info("BaseParser LLM result | dates=%d | obligations=%d", len(out_dates), len(out_obs))
                return out_dates, out_obs
        except Exception as e:
            logger.warning("BaseParser: LLM call/parse failed -> escalate | error=%r", e)
        logger.info("BaseParser: returning empty to trigger human escalation")
        return [], []

    def _llm_json(self, system_prompt: str, user_parts: List[dict]) -> Optional[dict]:
        """Call OpenAI chat with structured JSON response. Returns dict or None on failure."""
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            logger.info("Parser LLM unavailable (openai import failed): %r", e)
            return None

        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        model = settings.OPENAI_MODEL or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            logger.info("Parser LLM not configured (no OPENAI_API_KEY)")
            return None

        try:
            client = OpenAI(api_key=api_key)  # type: ignore
            # diagnostics
            text_part = next((p for p in user_parts if p.get("type") == "text"), None)
            text_len = len(text_part.get("text", "")) if isinstance(text_part, dict) else 0
            img_count = sum(1 for p in user_parts if p.get("type") == "image_url")
            logger.info("Parser LLM call | model=%s | text_len=%d | images=%d", model, text_len, img_count)
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_parts},
                ],
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content or "{}"
            logger.debug("Parser LLM raw response: %s", content)
        except Exception as e:
            logger.warning("Parser LLM call failed: %r", e)
            return None

        try:
            return json.loads(content)
        except Exception as e:
            logger.warning("Parser LLM JSON parse failed: %r", e)
            return None

    @staticmethod
    def _find_dates(text: str) -> List[datetime]:
        dates = []
        for match in re.finditer(r"\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\w+ \d{1,2}, \d{4})\b", text):
            try:
                dates.append(dateparser.parse(match.group(0), fuzzy=True))
            except Exception:
                continue
        return dates
