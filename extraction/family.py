"""Extract only explicit, two-name kinship statements from the news corpus."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from ner_link import NAME_RE

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
CORPUS = ROOT / "data" / "interim" / "news_docs.jsonl"

BETWEEN = re.compile(
    r"^\s*(?:,\s*)?(?:là\s+)?(?P<kin>con trai|con gái|cha|bố|mẹ|vợ|chồng|anh trai|chị gái|em trai|em gái)\s+của\s+(?:ông\s+|bà\s+)?$",
    re.I,
)


def family_relation(first_id: str, second_id: str, words: str):
    m = BETWEEN.fullmatch(words)
    if not m or first_id == second_id:
        return None
    kin = m.group("kin").lower()
    if kin in ("con trai", "con gái"):
        return second_id, "PARENT_OF", first_id
    if kin in ("cha", "bố", "mẹ"):
        return first_id, "PARENT_OF", second_id
    if kin in ("vợ", "chồng"):
        return min(first_id, second_id), "SPOUSE_OF", max(first_id, second_id)
    return min(first_id, second_id), "SIBLING_OF", max(first_id, second_id)


def unique_people() -> dict[str, str]:
    names = defaultdict(set)
    for path in (PROC / "nodes_person.csv", PROC / "nodes_person_news.csv"):
        if path.exists():
            with path.open(encoding="utf-8") as source:
                for row in csv.DictReader(source):
                    names[row["name"]].add(row["id"])
    return {name: next(iter(ids)) for name, ids in names.items() if len(ids) == 1}


def run() -> tuple[int, int]:
    people = unique_people()
    relations = {}
    candidates = []
    with CORPUS.open(encoding="utf-8") as source:
        for line in source:
            doc = json.loads(line)
            for sentence in doc["sents"]:
                if not any(k in sentence.lower() for k in ("của", "vợ", "chồng")):
                    continue
                mentions = [(m.start(), m.end(), people[m.group(0)]) for m in NAME_RE.finditer(sentence)
                            if m.group(0) in people]
                if len(mentions) != 2:
                    continue
                a, b = mentions
                result = family_relation(a[2], b[2], sentence[a[1]:b[0]])
                if not result:
                    continue
                src, rel, dst = result
                candidate = {"src": src, "src_label": "Person", "rel": rel,
                             "dst": dst, "dst_label": "Person", "source": doc["url"],
                             "evidence": sentence[:500], "date": doc["date"],
                             "method": "rule:explicit_kinship", "confidence": 0.8,
                             "review_status": "candidate"}
                candidates.append(candidate)
                relations.setdefault((src, rel, dst), candidate)
    out = PROC / "edges_family.csv"
    fields = ["src", "src_label", "rel", "dst", "dst_label", "source", "evidence",
              "date", "method", "confidence", "review_status"]
    with out.open("w", encoding="utf-8", newline="") as dest:
        writer = csv.DictWriter(dest, fieldnames=fields)
        writer.writeheader()
        writer.writerows(relations.values())
    return len(candidates), len(relations)


if __name__ == "__main__":
    mentions, edges = run()
    print(f"Explicit kinship mentions: {mentions}; unique candidate edges: {edges}")
