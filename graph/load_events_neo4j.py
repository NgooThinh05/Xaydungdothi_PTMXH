# -*- coding: utf-8 -*-
"""
Nạp các Nút Sự kiện (:Event) và Cạnh liên kết vào CSDL Neo4j đang chạy.
"""

import csv
import os
import sys
from pathlib import Path

ROOT = Path("E:/MXH/ck")
GRAPH_DIR = ROOT / "data" / "processed" / "graph"

from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "mxh-password")
BATCH = 2000


def clean_props(d):
    return {k: v for k, v in d.items() if v not in (None, "")}


def chunks(lst, n=BATCH):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def load_events():
    node_file = GRAPH_DIR / "nodes_event.csv"
    edge_file = GRAPH_DIR / "edges_event.csv"

    if not node_file.exists() or not edge_file.exists():
        print(f"File {node_file} or {edge_file} not found yet!")
        return

    with open(node_file, "r", encoding="utf-8") as f:
        nodes = [clean_props(r) for r in csv.DictReader(f)]

    with open(edge_file, "r", encoding="utf-8") as f:
        edges = [clean_props(r) for r in csv.DictReader(f)]

    print(f"Loaded {len(nodes)} Event nodes and {len(edges)} Event edges from CSV.")

    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        # Create constraint / index
        session.run("CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE")
        session.run("CREATE INDEX event_type_idx IF NOT EXISTS FOR (e:Event) ON (e.event_type)")

        # Load nodes
        print("Inserting :Event nodes into Neo4j...")
        for batch in chunks(nodes, BATCH):
            session.run("""
                UNWIND $batch AS row
                MERGE (e:Event {id: row.id})
                SET e += row
            """, batch=batch)

        # Load edges (Pure Cypher, không phụ thuộc APOC)
        print("Inserting Event relationships into Neo4j (Pure Cypher)...")
        agent_to_event = [e for e in edges if e.get("dst_label") == "Event"]
        event_to_target = [e for e in edges if e.get("src_label") == "Event"]

        print(f"  -> Agent -> Event edges: {len(agent_to_event)}")
        for batch in chunks(agent_to_event, BATCH):
            session.run("""
                UNWIND $batch AS row
                MATCH (s {id: row.src})
                MATCH (e:Event {id: row.dst})
                MERGE (s)-[r:KHOI_TAO_SU_KIEN]->(e)
                ON CREATE SET r.event_type = row.event_type, r.weight = toFloat(row.weight)
            """, batch=batch)

        print(f"  -> Event -> Target edges: {len(event_to_target)}")
        for batch in chunks(event_to_target, BATCH):
            session.run("""
                UNWIND $batch AS row
                MATCH (e:Event {id: row.src})
                MATCH (t {id: row.dst})
                MERGE (e)-[r:TAC_DONG_TOI]->(t)
                ON CREATE SET r.event_type = row.event_type, r.weight = toFloat(row.weight)
            """, batch=batch)

        # Count
        event_count = session.run("MATCH (e:Event) RETURN count(e) AS cnt").single()["cnt"]
        print(f"Total :Event nodes now in Neo4j: {event_count}")

    driver.close()
    print("Event graph loaded into Neo4j successfully!")


if __name__ == "__main__":
    load_events()
