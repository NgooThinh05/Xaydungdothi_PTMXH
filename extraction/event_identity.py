"""Stable identity for a news assertion; publication time is not event time."""
from __future__ import annotations

import hashlib
import re
from datetime import date


EVENT_RELS = {
    "CHU_TRI", "CHI_DAO", "BO_NHIEM", "DIEU_DONG", "MIEN_NHIEM",
    "THANH_TRA", "KIEM_TRA", "KY_LUAT", "LAM_VIEC_VOI", "PHOI_HOP",
}
DATE_RE = re.compile(r"\b(?:ngày\s+)?(\d{1,2})\s*[/-]\s*(\d{1,2})\s*[/-]\s*(20\d{2}|19\d{2})\b|\bngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(20\d{2}|19\d{2})\b", re.I)


def explicit_event_date(sentence: str) -> str:
    """Return an explicit full date in the evidence sentence, or empty string."""
    for match in DATE_RE.finditer(sentence):
        d, m, y = match.group(1, 2, 3) if match.group(1) else match.group(4, 5, 6)
        try:
            return date(int(y), int(m), int(d)).isoformat()
        except ValueError:
            continue
    return ""


def assertion_id(doc_id: str, sent_idx: int, rel: str, src: str, dst: str, trigger: str) -> str:
    """Keep distinct source sentences; collapse exact reruns of the same assertion."""
    raw = "\x1f".join((doc_id, str(sent_idx), rel, src, dst, trigger))
    return "evt:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
