"""Nạp nút & cạnh (CSV trong data/processed/) vào Neo4j.

Cách dùng:
  python graph/build_graph.py             # (trước đó) dựng bảng đồ thị cuối -> data/processed/graph/
  python graph/load_neo4j.py              # nạp (MERGE, chạy lại không bị trùng)
  python graph/load_neo4j.py --reset      # xoá toàn bộ đồ thị rồi nạp lại

Đọc mọi file edges_*.csv (edges_wiki.csv, edges_news.csv ...) nên các bước
trích xuất quan hệ từ tin tức chỉ cần ghi thêm file cùng định dạng.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
load_dotenv(ROOT / ".env")

# Bảng đồ thị cuối do graph/build_graph.py sinh ra (đã khử trùng, mô hình Người – Chức vụ – Cơ quan)
GRAPH_DIR = PROC / "graph"
NODE_FILES = {"Person": ["nodes_person.csv"], "Organization": ["nodes_org.csv"],
              "ChucVu": ["nodes_position.csv"], "Province": ["nodes_province.csv"]}
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
        elif k in ("birth_year", "news_article_count") and v.isdigit():
            v = int(v)
        elif k == "confidence":
            v = float(v)
        elif k == "weight":
            v = int(float(v))
        out[k] = v
    return out


def run_cypher_file(session, path: Path):
    """Chạy lần lượt các câu lệnh (kết thúc bằng ';' ở cuối dòng) trong file .cypher, bỏ dòng chú thích //."""
    text = "\n".join(l for l in path.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("//"))
    for stmt in re.split(r";[ \t]*$", text, flags=re.M):  # chỉ tách ở ';' cuối dòng (chuỗi có thể chứa ';')
        stmt = stmt.strip()
        if stmt:
            session.run(stmt).consume()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    drv = GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                               auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "mxh-password")))
    with drv.session() as s:
        if args.reset:
            s.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 5000 ROWS").consume()
        run_cypher_file(s, ROOT / "graph" / "cypher" / "schema.cypher")

        for label, fnames in NODE_FILES.items():
            rows = [clean_props(r) for f in fnames if (GRAPH_DIR / f).exists() for r in read(GRAPH_DIR / f)]
            for ch in chunks(rows):
                s.run(f"UNWIND $rows AS r MERGE (n:{label} {{id: r.id}}) SET n += r", rows=ch).consume()
            print(f"  {label:13s} {len(rows)}")

        for ef in sorted(GRAPH_DIR.glob("edges*.csv")):
            groups = defaultdict(list)
            for r in read(ef):
                groups[(r["src_label"], r["rel"], r["dst_label"], bool(r.get("event_id")))].append(
                    {"src": r["src"], "dst": r["dst"], "props": clean_props(r, drop=("src", "dst", "src_label", "dst_label", "rel"))})
            for (sl, rel, dl, has_event_id), rows in groups.items():
                key = ("event_id: r.props.event_id" if has_event_id else
                       "role: coalesce(r.props.role, ''), start: coalesce(r.props.start, '')")
                q = (f"UNWIND $rows AS r MATCH (a:{sl} {{id: r.src}}) MATCH (b:{dl} {{id: r.dst}}) "
                     f"MERGE (a)-[e:{rel} {{{key}}}]->(b) SET e += r.props")
                for ch in chunks(rows):
                    s.run(q, rows=ch).consume()
            print(f"  {ef.name}: {sum(len(v) for v in groups.values())} cạnh, {len({k[1] for k in groups})} loại")

        run_cypher_file(s, ROOT / "graph" / "cypher" / "display.cypher")  # nhãn hiển thị cho Browser
        print("  thuộc tính hiển thị: hien_thi (nút), nhan (cạnh)")

        n = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        m = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        print(f"Neo4j: {n} nút, {m} cạnh")
    drv.close()


if __name__ == "__main__":
    main()
