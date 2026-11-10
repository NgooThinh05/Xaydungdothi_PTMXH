"""Validate generated CSVs before loading them into Neo4j."""
from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path

GRAPH = Path(__file__).resolve().parents[1] / "data" / "processed" / "graph"
FILES = {"Person": "nodes_person.csv", "Organization": "nodes_org.csv",
         "ChucVu": "nodes_position.csv", "Province": "nodes_province.csv"}


def read(name: str):
    with (GRAPH / name).open(encoding="utf-8") as source:
        return list(csv.DictReader(source))


def validate() -> dict:
    nodes = {label: {row["id"] for row in read(name)} for label, name in FILES.items()}
    edges = read("edges.csv")
    problems = []
    event_ids = set()
    pairs = Counter()
    for index, row in enumerate(edges, 2):
        for end in ("src", "dst"):
            label = row[end + "_label"]
            if label not in nodes or row[end] not in nodes[label]:
                problems.append(f"edges.csv:{index}: missing {end} {label}/{row[end]}")
        event_id = row.get("event_id", "")
        if event_id:
            if event_id in event_ids:
                problems.append(f"edges.csv:{index}: duplicate event_id {event_id}")
            event_ids.add(event_id)
            pairs[(row["src"], row["rel"], row["dst"])] += 1
        event_date = row.get("event_date", "")
        if event_date:
            try:
                date.fromisoformat(event_date)
            except ValueError:
                problems.append(f"edges.csv:{index}: invalid event_date {event_date}")
    if problems:
        raise ValueError("\n".join(problems[:20]))
    people = read("nodes_person.csv")
    return {"nodes": {k: len(v) for k, v in nodes.items()}, "edges": len(edges),
            "event_assertions": len(event_ids),
            "pairs_with_multiple_assertions": sum(n > 1 for n in pairs.values()),
            "people_without_edges": sum(p.get("verification_status") == "needs_review" for p in people)}


if __name__ == "__main__":
    import json
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
