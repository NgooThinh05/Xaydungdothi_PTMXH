"""Chuẩn hoá văn bản tiếng Việt & tách câu (không cần thư viện ngoài)."""
from __future__ import annotations

import re
import unicodedata

# Kiểu bỏ dấu cũ (oà, uỷ) -> kiểu mới (òa, ủy) để khớp gazetteer ổn định
_TONE_FIX = {}
for base, tones in (("oa", "àáảãạ"), ("oe", "èéẻẽẹ"), ("uy", "ỳýỷỹỵ")):
    plain = {"oa": "a", "oe": "e", "uy": "y"}[base]
    first = {"oa": "òóỏõọ", "oe": "òóỏõọ", "uy": "ùúủũụ"}[base]
    for t_old, t_new in zip(tones, first):
        old = base[0] + t_old
        new = t_new + plain
        _TONE_FIX[old] = new
        _TONE_FIX[old[0].upper() + old[1:]] = new[0].upper() + new[1:]
_TONE_RE = re.compile(r"(?<![qQ])(" + "|".join(map(re.escape, _TONE_FIX)) + r")(?![\w])")
# "Uỷ" xuất hiện cả giữa từ ghép ("Uỷ ban") -> sửa riêng
_EXTRA = {"Uỷ": "Ủy", "uỷ": "ủy", "Thuỷ": "Thủy", "thuỷ": "thủy", "Hoá": "Hóa", "hoá": "hóa", "Thoả": "Thỏa", "thoả": "thỏa"}


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "")
    s = s.replace("\u00a0", " ").replace("\u200b", "")
    for a, b in _EXTRA.items():
        s = s.replace(a, b)
    s = _TONE_RE.sub(lambda m: _TONE_FIX[m.group(1)], s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


_ABBR = ["TP.", "Tp.", "TS.", "ThS.", "PGS.", "GS.", "BS.", "KS.", "Th.S", "St.", "Mr.", "Dr.", "v.v.", "Q.", "P."]
_SPLIT = re.compile(r"(?:(?<=[.!?…])|(?<=[.!?…][\"”’)]))\s+(?=[\"“(]?[A-ZĐÀ-Ỹ0-9])")


def split_sentences(text: str) -> list[str]:
    out = []
    for para in re.split(r"\n+", text or ""):
        para = para.strip()
        if len(para) < 15:
            continue
        p = para
        for i, a in enumerate(_ABBR):
            p = p.replace(a + " ", a.replace(".", f"§{i}§") + " ").replace(a, a.replace(".", f"§{i}§"))
        for s in _SPLIT.split(p):
            s = re.sub(r"§\d+§", ".", s).strip()
            if 15 <= len(s) <= 1500:
                out.append(s)
    return out


def slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s.replace("Đ", "D").replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
