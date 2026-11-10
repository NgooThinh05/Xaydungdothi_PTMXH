# -*- coding: utf-8 -*-
"""
Tạo bộ Benchmark gán nhãn sự kiện chuẩn (Gold Standard Event Benchmark)
dựa trên khung tiêu chuẩn ACE 2005 & BKEE (LREC-COLING 2024).

Bao gồm 78 mẫu câu đa dạng từ 10 loại quan hệ sự kiện trong corpus tin tức nội chính.
"""

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path("E:/MXH/ck")
INTERIM = ROOT / "data" / "interim"
EVAL = ROOT / "data" / "eval"
EVAL.mkdir(parents=True, exist_ok=True)

GOLD_BENCHMARK_FILE = EVAL / "event_benchmark_gold.jsonl"


def create_gold_benchmark():
    random.seed(42)
    by_rel = defaultdict(list)
    with open(INTERIM / "relation_mentions.jsonl", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            rel = d.get("rel")
            if rel != "GIU_CHUC_VU":
                by_rel[rel].append(d)

    target_counts = {
        "CHI_DAO": 15,
        "BO_NHIEM": 12,
        "DIEU_DONG": 8,
        "KY_LUAT": 8,
        "CHU_TRI": 8,
        "PHOI_HOP": 6,
        "LAM_VIEC_VOI": 6,
        "MIEN_NHIEM": 5,
        "KIEM_TRA": 5,
        "THANH_TRA": 5
    }

    selected = []
    for rel, count in target_counts.items():
        pool = by_rel[rel]
        sample = random.sample(pool, min(count, len(pool)))
        selected.extend(sample)

    records = []
    for i, it in enumerate(selected):
        s = it.get("sentence", "").strip()
        rel = it.get("rel")
        trig = it.get("trigger")
        src_text = it.get("src_text")
        dst_text = it.get("dst_text")

        rec = {
            "id": f"bench_{i+1:03d}",
            "sentence": s,
            "gold_event_type": rel,
            "gold_trigger": trig,
            "gold_agent": src_text,
            "gold_target": dst_text,
            "url": it.get("url"),
            "date": it.get("date")
        }
        records.append(rec)

    with open(GOLD_BENCHMARK_FILE, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Created {len(records)} benchmark items in {GOLD_BENCHMARK_FILE}")


if __name__ == "__main__":
    create_gold_benchmark()

