"""Thống kê mạng đã nạp trong Neo4j -> report/stats.md + report/figures/*.png

Chỉ số: số nút/cạnh theo loại, bậc (min/avg/max), mật độ, thành phần liên thông,
hệ số phân cụm, đường đi ngắn nhất trung bình & đường kính (thành phần lớn nhất,
xấp xỉ bằng lấy mẫu), top-k theo bậc & PageRank.
"""
from __future__ import annotations

import os
import random
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from neo4j import GraphDatabase  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
FIG = REPORT / "figures"
load_dotenv(ROOT / ".env")


def main():
    drv = GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                               auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "mxh-password")))
    with drv.session() as s:
        nodes = s.run("MATCH (n) RETURN n.id AS id, labels(n)[0] AS label, n.name AS name, n.type AS type").data()
        edges = s.run("MATCH (a)-[r]->(b) RETURN a.id AS s, b.id AS t, type(r) AS rel").data()
    drv.close()

    G = nx.MultiDiGraph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        G.add_edge(e["s"], e["t"], rel=e["rel"])
    U = nx.Graph(G.to_undirected())

    lab = Counter(n["label"] for n in nodes)
    rel = Counter(e["rel"] for e in edges)
    org_t = Counter(n["type"] for n in nodes if n["label"] == "Organization")
    degs = [d for _, d in U.degree()]
    comps = sorted(nx.connected_components(U), key=len, reverse=True)
    giant = U.subgraph(comps[0]).copy()
    random.seed(0)
    sample = random.sample(list(giant.nodes), min(300, giant.number_of_nodes()))
    lens, ecc = [], []
    for v in sample:
        d = nx.single_source_shortest_path_length(giant, v)
        lens += list(d.values())
        ecc.append(max(d.values()))
    pr = nx.pagerank(nx.DiGraph(G))
    name = {n["id"]: n["name"] for n in nodes}
    label = {n["id"]: n["label"] for n in nodes}

    L = ["# Thống kê mạng", "",
         f"- Tổng số nút: **{G.number_of_nodes()}**, tổng số cạnh: **{G.number_of_edges()}**, số loại cạnh: **{len(rel)}**",
         f"- Bậc (vô hướng, gộp cạnh song song): min {min(degs)}, trung bình {sum(degs)/len(degs):.2f}, max {max(degs)}",
         f"- Mật độ (đồ thị vô hướng đơn): {nx.density(U):.5f}",
         f"- Số thành phần liên thông: {len(comps)}; thành phần lớn nhất: {len(comps[0])} nút "
         f"({100*len(comps[0])/U.number_of_nodes():.1f}%); số nút cô lập: {sum(1 for d in degs if d == 0)}",
         f"- Hệ số phân cụm trung bình: {nx.average_clustering(U):.4f}; transitivity: {nx.transitivity(U):.4f}",
         f"- Độ dài đường đi ngắn nhất trung bình (TPLT lớn nhất, mẫu 300 nút): {sum(lens)/len(lens):.2f}; "
         f"đường kính xấp xỉ: {max(ecc)}", "",
         "## Nút theo nhãn", "", "| Nhãn | Số lượng |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in lab.most_common()]
    L += ["", "## Cơ quan theo loại", "", "| Loại | Số lượng |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in org_t.most_common()]
    L += ["", "## Cạnh theo loại quan hệ", "", "| Quan hệ | Số lượng |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in rel.most_common()]
    for title, lbl in (("Top 20 chính trị gia theo bậc", "Person"), ("Top 20 cơ quan theo bậc", "Organization")):
        top = sorted((v for v in U.nodes if label[v] == lbl), key=U.degree, reverse=True)[:20]
        L += ["", f"## {title}", "", "| # | Tên | Bậc | PageRank |", "|---|---|---|---|"]
        L += [f"| {i} | {name[v]} | {U.degree(v)} | {pr[v]:.5f} |" for i, v in enumerate(top, 1)]
    REPORT.mkdir(exist_ok=True)
    (REPORT / "stats.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ks, vs = zip(*rel.most_common())
    ax.barh(ks[::-1], vs[::-1], color="#3b6ea5")
    ax.set_xlabel("Số cạnh")
    ax.set_title("Số cạnh theo loại quan hệ")
    fig.tight_layout()
    fig.savefig(FIG / "edges_by_type.png", dpi=150)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    c = Counter(degs)
    ax.loglog(list(c.keys()), list(c.values()), "o", ms=4, color="#3b6ea5")
    ax.set_xlabel("Bậc k")
    ax.set_ylabel("Số nút có bậc k")
    ax.set_title("Phân phối bậc (log-log)")
    fig.tight_layout()
    fig.savefig(FIG / "degree_distribution.png", dpi=150)
    print("\n".join(L[:9]))
    print(f"-> {REPORT/'stats.md'}, {FIG}")


if __name__ == "__main__":
    main()
