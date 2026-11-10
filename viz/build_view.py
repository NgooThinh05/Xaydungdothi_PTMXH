"""Xuất toàn bộ đồ thị từ Neo4j -> viz/graph_data.js để xem trên một màn hình (viz/index.html).

Bố cục (toạ độ x, y) được tính sẵn bằng thuật toán lực Fruchterman–Reingold (networkx),
nên trang mở ra là thấy ngay toàn mạng, không cần chờ mô phỏng.

    cd viz && npm install --no-bin-links && cd ..   # một lần: gói graphology cho ForceAtlas2
    python viz/build_view.py                         # xuất dữ liệu + bố cục FR -> tinh chỉnh ForceAtlas2
    xdg-open viz/index.html                          # mở bằng trình duyệt (chạy được offline)
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import time
from pathlib import Path

import networkx as nx
from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
OUT = ROOT / "viz" / "graph_data.js"

PARTY = ("Cơ quan lãnh đạo Đảng", "Cơ quan Đảng TW", "Đảng ủy", "Ban Chỉ đạo")
CENTRAL_STATE = ("Thiết chế nhà nước", "Quốc hội", "Cơ quan Quốc hội", "Bộ", "Cơ quan ngang bộ",
                 "Cơ quan tư pháp/kiểm toán", "Đơn vị thuộc bộ", "Đơn vị sự nghiệp", "Doanh nghiệp nhà nước",
                 "Cơ quan báo chí", "Lực lượng vũ trang", "Mặt trận & đoàn thể")


def group(n: dict) -> str:
    if n["label"] == "Person":
        return "person"
    if n["label"] == "Province":
        return "province"
    if n["label"] == "ChucVu":
        return "position"
    t, lvl = n.get("type") or "", n.get("level") or ""
    if lvl in ("Tỉnh", "Huyện") or t in ("Cấp ủy tỉnh", "Cơ quan Đảng tỉnh", "UBND tỉnh", "HĐND tỉnh", "Sở",
                                          "Công an tỉnh", "Đoàn ĐBQH tỉnh", "Cơ quan cấp tỉnh") or t.startswith("Cấp ủy huyện"):
        return "org_local"
    if t in PARTY:
        return "org_party"
    return "org_central"


def main():
    t0 = time.time()
    drv = GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                               auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "mxh-password")))
    with drv.session() as s:
        nodes = s.run("MATCH (n) RETURN n.id AS id, labels(n)[0] AS label, n.name AS name, n.type AS type, "
                      "coalesce(n.hien_thi, n.name) AS hien_thi, n.level AS level, n.province AS province, n.birth_year AS birth_year, n.source AS src, n.chuc_vu AS cv").data()
        edges = s.run("MATCH (a)-[r]->(b) RETURN a.id AS s, b.id AS t, type(r) AS rel, r.role AS role, r.start AS start, "
                      "r.end AS end, r.date AS date, r.weight AS w, r.source AS source, r.evidence AS ev, "
                      "r.method AS method, r.nhan AS nhan").data()
    drv.close()

    G = nx.Graph()
    G.add_nodes_from(n["id"] for n in nodes)
    for e in edges:
        if e["s"] != e["t"]:
            w = G.get_edge_data(e["s"], e["t"], {}).get("weight", 0)
            G.add_edge(e["s"], e["t"], weight=w + 1)
    deg = dict(G.degree())
    print(f"đọc {len(nodes)} nút, {len(edges)} cạnh ({time.time() - t0:.1f}s); tính bố cục ...")
    pos = nx.spring_layout(G, k=1.6 / math.sqrt(G.number_of_nodes()), iterations=80, seed=7, weight=None)
    print(f"bố cục xong ({time.time() - t0:.1f}s)")

    N = []
    for n in nodes:
        x, y = pos[n["id"]]
        N.append({"id": n["id"], "n": (n["hien_thi"] if n["label"] == "ChucVu" else n["name"]) or n["id"], "g": group(n), "ty": n.get("type") or n["label"],
                  "p": n.get("province") or "", "cv": n.get("cv") or "", "by": n.get("birth_year") or "", "news": n.get("src") == "news",
                  "d": deg.get(n["id"], 0), "x": round(float(x) * 1000, 2), "y": round(float(y) * 1000, 2)})
    E = []
    for e in edges:
        news = (e["method"] or "").startswith("rule") or (e["source"] or "").startswith("http")
        E.append({"s": e["s"], "t": e["t"], "r": e["rel"], "ro": e["role"] or "", "st": e["start"] or "",
                  "en": e["end"] or "", "dt": e["date"] or "", "w": e["w"] or 1, "nw": news,
                  "src": (e["source"] or "") if news else (e["source"] or "")[:80],
                  "ev": (e["ev"] or "")[:320], "nh": e.get("nhan") or ""})
    OUT.write_text("window.GRAPH = " + json.dumps({"nodes": N, "edges": E}, ensure_ascii=False, separators=(",", ":"))
                   + ";\n", encoding="utf-8")
    print(f"-> {OUT} ({OUT.stat().st_size / 1e6:.1f} MB, {time.time() - t0:.1f}s)")
    # Tinh chỉnh bố cục bằng ForceAtlas2 (Barnes-Hut, LinLog) nếu có Node.js + gói graphology
    viz = OUT.parent
    if shutil.which("node") and (viz / "node_modules" / "graphology-layout-forceatlas2").exists():
        subprocess.run(["node", "layout_fa2.mjs", "1200", "linlog"], cwd=viz, check=True)
    else:
        print("(bỏ qua ForceAtlas2: cần `cd viz && npm install --no-bin-links`)")


if __name__ == "__main__":
    main()
