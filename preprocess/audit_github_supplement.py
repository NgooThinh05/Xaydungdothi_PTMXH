"""Đối chiếu bộ dữ liệu GitHub bổ sung với thực thể hiện hành.

Script không sửa các CSV chuẩn và không nạp Neo4j. Nó xuất hai bảng ứng viên để
kiểm duyệt/liên kết thực thể trước khi nhập dữ liệu của dự án khác.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "data" / "external" / "xaydungdothi_ptmxh"
PROFILES = EXTERNAL / "baomoi_vn_politicians_profiles.csv"
EDGES = EXTERNAL / "baomoi_vn_politicians_edges.csv"
OUT = ROOT / "data" / "interim"
COMMIT = "93f8358f86edfef8803af6d20e922271da6c7659"


def key(value: str | None) -> str:
    value = unicodedata.normalize("NFC", value or "").strip().casefold()
    return re.sub(r"\s+", " ", value)


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def local_people() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for filename in ("nodes_person.csv", "nodes_person_news.csv"):
        path = ROOT / "data" / "processed" / filename
        if not path.exists():
            continue
        for row in read_csv(path):
            name = key(row.get("name"))
            identifier = row.get("id") or row.get("person_id") or ""
            if name and identifier:
                result.setdefault(name, []).append(identifier)
    return result


def write_rows(path: Path, fieldnames: list[str], rows: list[dict]):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    people = local_people()
    profiles = []
    statuses = Counter()
    for row in read_csv(PROFILES):
        ids = people.get(key(row.get("person_name")), [])
        status = "matched_unique" if len(ids) == 1 else "matched_ambiguous" if ids else "new_candidate"
        statuses[status] += 1
        profiles.append({
            "person_name": row.get("person_name", ""),
            "match_status": status,
            "local_ids": " | ".join(ids),
            "role_title": row.get("role_title", ""),
            "organization": row.get("organization", ""),
            "province": row.get("province", ""),
            "total_articles": row.get("total_articles", ""),
            "total_mentions": row.get("total_mentions", ""),
            "main_character_count": row.get("main_character_count", ""),
            "sample_article_titles": row.get("sample_article_titles", ""),
            "source_commit": COMMIT,
            "review_status": "pending",
        })

    profile_fields = list(profiles[0]) if profiles else []
    write_rows(OUT / "github_profile_candidates.csv", profile_fields, profiles)

    edge_rows = []
    edge_statuses = Counter()
    for row in read_csv(EDGES):
        source_ids = people.get(key(row.get("source_person")), [])
        target_ids = people.get(key(row.get("target_person")), [])
        if len(source_ids) == 1 and len(target_ids) == 1:
            status = "both_matched"
        elif source_ids or target_ids:
            status = "one_or_ambiguous"
        else:
            status = "both_unmatched"
        edge_statuses[status] += 1
        edge_rows.append({
            **row,
            "source_local_ids": " | ".join(source_ids),
            "target_local_ids": " | ".join(target_ids),
            "match_status": status,
            "source_commit": COMMIT,
            "review_status": "pending",
        })
    edge_fields = list(edge_rows[0]) if edge_rows else []
    write_rows(OUT / "github_cooccurrence_candidates.csv", edge_fields, edge_rows)

    summary = {
        "source_commit": COMMIT,
        "profiles": len(profiles),
        "profile_status": dict(statuses),
        "cooccurrence_edges": len(edge_rows),
        "edge_status": dict(edge_statuses),
        "note": "Co-occurrence is not a direction, command or kinship relation.",
    }
    (OUT / "github_supplement_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
