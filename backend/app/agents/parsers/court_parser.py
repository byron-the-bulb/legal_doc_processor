from __future__ import annotations
import logging
from typing import List, Tuple, Optional

from dateutil import parser as dateparser
from app.models.schemas import ExtractedDate, LegalObligation
from .base_parser import BaseParser, _encode_images_as_data_urls


logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)


class CourtParser(BaseParser):
    name = "court"

    def parse(self, text: str, images: Optional[List[str]] = None) -> Tuple[List[ExtractedDate], List[LegalObligation]]:
        # Try LLM-first
        try:
            image_urls = _encode_images_as_data_urls(images or []) if images else []
            system_prompt = (
                "You are a legal parsing agent specialized in COURT ORDERS and SCHEDULING ORDERS. "
                "Using the extracted text and any provided page images, extract key dates and obligations.\n\n"
                "Return ONLY JSON with fields: \n"
                "- dates: array of {date_iso (ISO8601), date_type (hearing|conference|trial|deadline), source_text}\n"
                "- obligations: array of {description, due_date_iso (ISO8601), responsible_party, priority_level}\n\n"
                "Rules: \n"
                "- Only include an obligation if a due_date is explicitly present; otherwise omit it.\n"
                "- Do not hallucinate. If not sure, leave arrays empty.\n"
            )
            user_parts: List[dict] = [
                {"type": "text", "text": (
                    "Task: Extract hearing/trial/conference dates and filing deadlines. "
                    "Also extract obligations (e.g., file motion, serve response) with due dates.\n\n"
                    "Extracted text (may be partial):\n" + (text or "")[:12000]
                )}
            ]
            for url in image_urls:
                user_parts.append({"type": "image_url", "image_url": {"url": url}})

            data = self._llm_json(system_prompt, user_parts)
            if data:
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
                                confidence_score=0.8,
                                source_text=str(d.get("source_text") or "court parser llm"),
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
                            priority_level=str(o.get("priority_level") or "high"),
                            associated_case="",
                            source_document="court",
                        )
                    )
                if out_dates or out_obs:
                    logger.info("CourtParser branch: LLM | dates=%d | obligations=%d", len(out_dates), len(out_obs))
                    return out_dates, out_obs
                else:
                    img_count = len(image_urls)
                    logger.info(
                        "CourtParser LLM result unusable | dates=%d | obligations=%d | images=%d",
                        len(out_dates),
                        len(out_obs),
                        img_count,
                    )
            else:
                logger.info("CourtParser LLM returned no data (None) -> likely call failure or JSON parse error")
        except Exception as e:
            logger.warning("CourtParser: LLM call/parse failed -> escalate | error=%r", e)
            logger.info("CourtParser: returning empty to trigger human escalation")
            return [], []

        # If we reach here, LLM did not provide usable output
        logger.info("CourtParser: no usable LLM output -> returning empty to trigger human escalation")
        return [], []
