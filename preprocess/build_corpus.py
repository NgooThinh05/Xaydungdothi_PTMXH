"""Gộp nguồn tin, chuẩn hóa, khử trùng và tách câu.

Nguồn chính:
* corpus Báo Mới của nhóm;
* các file do ``crawler/crawl_news.py`` sinh;
* ``targeted_news.jsonl`` do crawler theo khoảng trống sinh;
* corpus ``5k_scrawl`` nếu có ở thư mục cha.

Đầu ra mỗi dòng gồm ``doc_id``, ``source``, ``url``, ``date``, ``title`` và
``sents``. Với bài crawl có mục tiêu còn giữ ``target_id``, ``query_kind``,
``query`` và ``discovery_backend`` để kiểm toán độ phủ.
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
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

POLITICAL = re.compile(
    r"Bí thư|Chủ tịch|Thủ tướng|Bộ trưởng|Thứ trưởng|UBND|Ủy ban|Tỉnh ủy|Thành ủy|"
    r"Quốc hội|Chính phủ|bổ nhiệm|kỷ luật|thanh tra|chủ trì|Ban Chỉ đạo|Giám đốc Sở|Đảng ủy"
)


def iso_date(value) -> str:
    if value in (None, ""):
        return ""
    text = str(value)
    if text.isdigit() and len(text) >= 9:
        return datetime.fromtimestamp(int(text), tz=timezone.utc).strftime("%Y-%m-%d")
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    return match.group(0) if match else ""


def _read_jsonl(path: Path):
    for line in path.open(encoding="utf-8", errors="ignore"):
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                yield value
        except json.JSONDecodeError:
            # Bỏ dòng cuối đang ghi dở, không làm hỏng cả corpus.
            continue


def sources():
    baomoi = NEWS / "baomoi" / "baomoi_political_corpus.jsonl"
    if baomoi.exists():
        for article in _read_jsonl(baomoi):
            yield {
                "source": "baomoi",
                "url": article.get("original_url") or article["baomoi_url"],
                "date": article.get("published_date"), "title": article.get("title"),
                "text": article.get("content") or "",
            }

    # Nhận tự động mọi đầu ra crawler ở thư mục gốc data/raw/news. Corpus
    # Báo Mới nằm trong thư mục con nên không bị đọc hai lần.
    for path in sorted(NEWS.glob("*.jsonl")):
        for article in _read_jsonl(path):
            if not article.get("url") or not article.get("text"):
                continue
            if article.get("target_match") == "name_only":
                continue  # giữ ở raw để rà soát người trùng tên trước khi nhập corpus
            source = article.get("site") or path.stem
            row = {
                "source": source, "url": article["url"], "date": article.get("date"),
                "title": article.get("title"), "text": article.get("text") or "",
            }
            for key in ("target_id", "target_name", "target_type", "target_context", "query_kind", "query",
                         "query_kinds", "queries", "discovery_backend", "retrieved_at", "target_match"):
                if article.get(key) not in (None, ""):
                    row[key] = article[key]
            yield row

    external = ROOT.parent / "5k_scrawl" / "articles_clean.jsonl"
    if external.exists():
        for article in _read_jsonl(external):
            text = article.get("text") or ""
            if len(POLITICAL.findall(text)) >= 3:
                yield {
                    "source": "5k_" + article["site"], "url": article["url"],
                    "date": article.get("date"), "title": article.get("title"), "text": text,
                }


def main():
    seen_url: dict[str, dict] = {}
    seen_title: dict[str, dict] = {}
    docs = []
    n_in = 0
    for article in sources():
        n_in += 1
        url = article["url"]
        title = norm_text(article.get("title") or "")
        title_key = re.sub(r"\W+", "", title.lower())
        existing = seen_url.get(url) or (seen_title.get(title_key) if title_key else None)
        if existing:
            # Một bài có thể được tìm thấy bởi nhiều mục tiêu. Giữ danh sách ID
            # thay vì nhân bản bài và câu trong corpus.
            target = article.get("target_id")
            if target:
                existing.setdefault("target_ids", [])
                if target not in existing["target_ids"]:
                    existing["target_ids"].append(target)
            continue
        text = norm_text(article.get("text") or "")
        if text.startswith(title):
            text = text[len(title):].lstrip()
        sentences = split_sentences(text)
        if not sentences:
            continue
        doc = {
            "doc_id": hashlib.md5(url.encode()).hexdigest()[:12],
            "source": article["source"], "url": url, "date": iso_date(article.get("date")),
            "title": title, "sents": sentences,
        }
        for key in ("target_id", "target_name", "target_type", "target_context", "query_kind", "query",
                     "query_kinds", "queries", "discovery_backend", "retrieved_at", "target_match"):
            if article.get(key) not in (None, ""):
                doc[key] = article[key]
        if article.get("target_id"):
            doc["target_ids"] = [article["target_id"]]
        docs.append(doc)
        seen_url[url] = doc
        if title_key:
            seen_title[title_key] = doc

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as output:
        for doc in docs:
            output.write(json.dumps(doc, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"{n_in} bài đầu vào -> {len(docs)} bài sau khử trùng, "
          f"{sum(len(x['sents']) for x in docs)} câu")
    print(Counter(x["source"] for x in docs))


if __name__ == "__main__":
    main()
