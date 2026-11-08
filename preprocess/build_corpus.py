"""Gộp các nguồn tin -> data/interim/news_docs.jsonl (đã chuẩn hoá, khử trùng lặp, tách câu).

Nguồn (bỏ qua nếu thiếu):
  data/raw/news/baomoi/baomoi_political_corpus.jsonl   (repo nhóm, 5.325 bài Báo Mới)
  data/raw/news/baochinhphu.jsonl, vnexpress.jsonl      (crawler/crawl_news.py)
  ../5k_scrawl/articles_clean.jsonl                     (5.000 bài đa chuyên mục, chỉ lấy bài có từ khoá chính trị)

Mỗi dòng đầu ra: {doc_id, source, url, date, title, sents: [..]}
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extraction"))
from textnorm import norm_text, split_sentences  # noqa: E402

NEWS = ROOT / "data" / "raw" / "news"
OUT = ROOT / "data" / "interim" / "news_docs.jsonl"

POLITICAL = re.compile(r"Bí thư|Chủ tịch|Thủ tướng|Bộ trưởng|Thứ trưởng|UBND|Ủy ban|Tỉnh ủy|Thành ủy|Quốc hội|Chính phủ|"
                       r"bổ nhiệm|kỷ luật|thanh tra|chủ trì|Ban Chỉ đạo|Giám đốc Sở|Đảng ủy")


def iso_date(v) -> str:
    if v is None or v == "":
        return ""
    s = str(v)
    if s.isdigit() and len(s) >= 9:  # unix timestamp (Báo Mới)
        return datetime.fromtimestamp(int(s), tz=timezone.utc).strftime("%Y-%m-%d")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    return m.group(0) if m else ""


def sources():
    p = NEWS / "baomoi" / "baomoi_political_corpus.jsonl"
    if p.exists():
        for l in p.open(encoding="utf-8"):
            a = json.loads(l)
            yield "baomoi", a.get("original_url") or a["baomoi_url"], a.get("published_date"), a.get("title"), \
                a.get("content") or ""
    for site in ("baochinhphu", "baochinhphu_search", "vnexpress"):
        p = NEWS / f"{site}.jsonl"
        if p.exists():
            for l in p.open(encoding="utf-8"):
                try:
                    a = json.loads(l)
                except json.JSONDecodeError:  # dòng cuối đang ghi dở khi crawler còn chạy
                    continue
                yield site, a["url"], a.get("date"), a.get("title"), a.get("text") or ""
    p = ROOT.parent / "5k_scrawl" / "articles_clean.jsonl"
    if p.exists():
        for l in p.open(encoding="utf-8"):
            a = json.loads(l)
            if len(POLITICAL.findall(a.get("text") or "")) >= 3:
                yield "5k_" + a["site"], a["url"], a.get("date"), a.get("title"), a.get("text") or ""


def main():
    seen_url, seen_title, n_in, docs = set(), set(), 0, []
    for src, url, date, title, text in sources():
        n_in += 1
        title = norm_text(title or "")
        key_t = re.sub(r"\W+", "", title.lower())
        if url in seen_url or (key_t and key_t in seen_title):
            continue
        seen_url.add(url); seen_title.add(key_t)
        text = norm_text(text)
        # bỏ dòng tiêu đề lặp ở đầu nội dung
        if text.startswith(title):
            text = text[len(title):].lstrip()
        sents = split_sentences(text)
        if not sents:
            continue
        docs.append({"doc_id": hashlib.md5(url.encode()).hexdigest()[:12], "source": src, "url": url,
                     "date": iso_date(date), "title": title, "sents": sents})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"{n_in} bài đầu vào -> {len(docs)} bài sau khử trùng, {sum(len(d['sents']) for d in docs)} câu")
    print(Counter(d["source"] for d in docs))


if __name__ == "__main__":
    main()
