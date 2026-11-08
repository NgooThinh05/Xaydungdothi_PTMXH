"""Bước 2 – Tải wikitext (kèm Wikidata QID) cho toàn bộ trang ứng viên.

Đầu vào : data/interim/wiki_candidates.json  (+ data/interim/expand_titles.json nếu có:
          các trang người được liên kết từ infobox nhưng chưa nằm trong thể loại gốc)
Đầu ra  : data/raw/wikipedia/pages.jsonl   (title, kind, pageid, wikidata, categories, wikitext)
          data/interim/redirects.json      (redirect -> tiêu đề chuẩn)
API     : action=query&prop=revisions|pageprops, 50 trang / request, có cache.
"""
from __future__ import annotations

import json
from pathlib import Path

from tqdm import tqdm

import wiki_client
from wiki_client import wikitext_batch

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "data" / "interim" / "wiki_candidates.json"
EXPAND = ROOT / "data" / "interim" / "expand_titles.json"
OUT = ROOT / "data" / "raw" / "wikipedia" / "pages.jsonl"
OUT_REDIR = ROOT / "data" / "interim" / "redirects.json"


def main():
    cand = json.loads(INP.read_text(encoding="utf-8"))
    if EXPAND.exists():
        for t in json.loads(EXPAND.read_text(encoding="utf-8")):
            cand.setdefault(t, {"kind": "person", "categories": ["(mở rộng từ infobox)"]})
    titles = sorted(cand)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    with OUT.open("w", encoding="utf-8") as f:
        for i in tqdm(range(0, len(titles), 50), desc="fetch"):
            pages = wikitext_batch(titles[i:i + 50])
            for title, p in pages.items():
                if title in seen:
                    continue
                seen.add(title)
                meta = cand.get(title) or {"kind": "person", "categories": ["(mở rộng từ infobox)"]}
                f.write(json.dumps({"title": title, **meta, **p}, ensure_ascii=False) + "\n")
    OUT_REDIR.write_text(json.dumps(wiki_client.REDIRECTS, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"Saved {len(seen)} pages -> {OUT}; {len(wiki_client.REDIRECTS)} redirects")


if __name__ == "__main__":
    main()
