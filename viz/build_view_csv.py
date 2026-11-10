"""Refresh the interactive HTML from validated graph CSVs without a Neo4j server."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "processed" / "graph"
OUT = ROOT / "viz" / "graph_data.js"

PARTY = ("Cơ quan lãnh đạo Đảng", "Cơ quan Đảng TW", "Đảng ủy", "Ban Chỉ đạo")
LOCAL_TYPES = ("Cấp ủy tỉnh", "Cơ quan Đảng tỉnh", "UBND tỉnh", "HĐND tỉnh", "Sở",
               "Công an tỉnh", "Đoàn ĐBQH tỉnh", "Cơ quan cấp tỉnh")


def read(name: str) -> list[dict]:
    with (GRAPH / name).open(encoding="utf-8") as source:
        return list(csv.DictReader(source))


def group(row: dict, label: str) -> str:
    if label == "Person":
        return "person"
    if label == "Province":
        return "province"
    if label == "ChucVu":
        return "position"
    if row.get("level") in ("Tỉnh", "Huyện") or row.get("type") in LOCAL_TYPES:
        return "org_local"
    if row.get("type") in PARTY:
        return "org_party"
    return "org_central"


def old_positions() -> dict[str, tuple[float, float]]:
    if not OUT.exists():
        return {}
    raw = OUT.read_text(encoding="utf-8")
    prefix = "window.GRAPH = "
    if not raw.startswith(prefix):
        return {}
    try:
        previous = json.loads(raw[len(prefix):].strip().rstrip(";"))
    except (ValueError, TypeError):
        return {}
    return {n["id"]: (float(n["x"]), float(n["y"])) for n in previous["nodes"]}


def seed_xy(node_id: str) -> tuple[float, float]:
    digest = hashlib.sha256(node_id.encode("utf-8")).digest()
    return ((int.from_bytes(digest[:4], "big") / 2**32 - .5) * 1800,
            (int.from_bytes(digest[4:8], "big") / 2**32 - .5) * 1800)


def build() -> dict[str, int]:
    nodes = [(label, row) for label, file in (("Person", "nodes_person.csv"),
             ("Organization", "nodes_org.csv"), ("ChucVu", "nodes_position.csv"),
             ("Province", "nodes_province.csv")) for row in read(file)]
    ids = {row["id"] for _, row in nodes}
    edges = [e for e in read("edges.csv") if e["src"] in ids and e["dst"] in ids]
    positions = {k: v for k, v in old_positions().items() if k in ids}
    neighbors: dict[str, list[str]] = defaultdict(list)
    degree: dict[str, int] = defaultdict(int)
    for e in edges:
        neighbors[e["src"]].append(e["dst"])
        neighbors[e["dst"]].append(e["src"])
        degree[e["src"]] += 1
        degree[e["dst"]] += 1
    for _ in range(2):
        for node_id in sorted(ids - positions.keys()):
            anchors = [positions[v] for v in neighbors[node_id] if v in positions]
            if anchors:
                jitter = seed_xy(node_id)
                positions[node_id] = (sum(x for x, _ in anchors) / len(anchors) + jitter[0] * .035,
                                      sum(y for _, y in anchors) / len(anchors) + jitter[1] * .035)
    for node_id in ids - positions.keys():
        positions[node_id] = seed_xy(node_id)

    out_nodes = []
    for label, row in nodes:
        node_id = row["id"]
        x, y = positions[node_id]
        out_nodes.append({"id": node_id, "n": (row.get("hien_thi") if label == "ChucVu" else row.get("name")) or node_id,
                          "g": group(row, label), "ty": row.get("type") or label,
                          "p": row.get("province") or "", "cv": row.get("chuc_vu") or "",
                          "by": row.get("birth_year") or "", "news": row.get("source") == "news",
                          "d": degree[node_id], "x": round(x, 2), "y": round(y, 2)})
    out_edges = []
    for e in edges:
        source = e.get("source") or ""
        is_news = bool(e.get("event_id")) or source.startswith("http")
        out_edges.append({"s": e["src"], "t": e["dst"], "r": e["rel"], "ro": e.get("role") or "",
                          "st": e.get("start") or "", "en": e.get("end") or "",
                          "dt": e.get("event_date") or e.get("date") or "", "w": e.get("weight") or 1,
                          "nw": is_news, "src": source if is_news else source[:80],
                          "ev": (e.get("evidence") or "")[:320], "nh": e.get("nhan") or ""})
    data = "window.GRAPH = " + json.dumps({"nodes": out_nodes, "edges": out_edges}, ensure_ascii=False,
                                               separators=(",", ":")) + ";\n"
    tmp = OUT.with_suffix(".js.tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(OUT)
    return {"nodes": len(out_nodes), "edges": len(out_edges)}


if __name__ == "__main__":
    print(build())
