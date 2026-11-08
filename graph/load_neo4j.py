"""Nạp nút & cạnh (CSV trong data/processed/) vào Neo4j.

Cách dùng:
  python graph/load_neo4j.py              # nạp (MERGE, chạy lại không bị trùng)
  python graph/load_neo4j.py --reset      # xoá toàn bộ đồ thị rồi nạp lại

Đọc mọi file edges_*.csv (edges_wiki.csv, edges_news.csv ...) nên các bước
trích xuất quan hệ từ tin tức chỉ cần ghi thêm file cùng định dạng.
"""
from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
load_dotenv(ROOT / ".env")

# Mỗi nhãn: file từ Wikipedia + file bổ sung từ tin tức (extraction/relations.py)
NODE_FILES = {"Person": ["nodes_person.csv", "nodes_person_news.csv"],
              "Organization": ["nodes_org.csv", "nodes_org_news.csv"],
              "Province": ["nodes_province.csv", "nodes_province_news.csv"]}
BATCH = 2000


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def chunks(rows, n=BATCH):
    for i in range(0, len(rows), n):
        yield rows[i:i + n]


def clean_props(r: dict, drop=()) -> dict:
    out = {}
    for k, v in r.items():
        if k in drop or v in ("", None):
            continue
        if v in ("True", "False"):
            v = v == "True"
        elif k in ("birth_year",) and v.isdigit():
            v = int(v)
        elif k == "confidence":
            v = float(v)
        elif k == "weight":
            v = int(float(v))
        out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    drv = GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                               auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "mxh-password")))
    with drv.session() as s:
        if args.reset:
            s.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 5000 ROWS").consume()
        for stmt in (ROOT / "graph" / "cypher" / "schema.cypher").read_text(encoding="utf-8").split(";"):
            stmt = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("//")).strip()
            if stmt:
                s.run(stmt).consume()

        for label, fnames in NODE_FILES.items():
            rows = [clean_props(r) for f in fnames if (PROC / f).exists() for r in read(PROC / f)]
            for ch in chunks(rows):
                s.run(f"UNWIND $rows AS r MERGE (n:{label} {{id: r.id}}) SET n += r", rows=ch).consume()
            print(f"  {label:13s} {len(rows)}")

        for ef in sorted(PROC.glob("edges_*.csv")):
            groups = defaultdict(list)
            for r in read(ef):
                groups[(r["src_label"], r["rel"], r["dst_label"])].append(
                    {"src": r["src"], "dst": r["dst"], "props": clean_props(r, drop=("src", "dst", "src_label", "dst_label", "rel"))})
            for (sl, rel, dl), rows in groups.items():
                # Khoá MERGE gồm role+start để giữ các nhiệm kỳ khác nhau là cạnh riêng
                q = (f"UNWIND $rows AS r MATCH (a:{sl} {{id: r.src}}) MATCH (b:{dl} {{id: r.dst}}) "
                     f"MERGE (a)-[e:{rel} {{role: coalesce(r.props.role, ''), start: coalesce(r.props.start, '')}}]->(b) "
                     f"SET e += r.props")
                for ch in chunks(rows):
                    s.run(q, rows=ch).consume()
            print(f"  {ef.name}: {sum(len(v) for v in groups.values())} cạnh, {len({k[1] for k in groups})} loại")

        n = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        m = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        print(f"Neo4j: {n} nút, {m} cạnh")
    drv.close()


if __name__ == "__main__":
    main()
