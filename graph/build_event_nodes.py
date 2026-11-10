# -*- coding: utf-8 -*-
"""
Module chuyển hóa quan hệ sự kiện thành Nút Sự kiện (Event Reification).
Sinh ra:
1. data/processed/graph/nodes_event.csv (Nút Event với action_content, deadline, legal_doc, role...)
2. data/processed/graph/edges_event.csv (Cạnh kết nối Agent -> Event -> Target)
3. Nạp bổ sung trực tiếp vào Neo4j (nhãn :Event) để có thể truy vấn ngay.
"""

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path("E:/MXH/ck")
INTERIM = ROOT / "data" / "interim"
GRAPH_DIR = ROOT / "data" / "processed" / "graph"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "extraction"))
from event_extractor import extract_event_arguments
from event_identity import assertion_id, explicit_event_date


def generate_event_nodes_and_edges():
    nodes_event = []
    edges_event = []

    seen_events = set()
    
    with open(INTERIM / "relation_mentions.jsonl", "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            d = json.loads(line)
            rel = d.get("rel")
            if rel == "GIU_CHUC_VU":
                continue # Giữ chức vụ là quan hệ cấu trúc, không phải sự kiện tin tức

            src = d.get("src")
            dst = d.get("dst")
            if not src or not dst:
                continue

            sent = d.get("sentence", "")
            trig = d.get("trigger", "")
            doc_id = d.get("doc_id", "doc")
            sent_idx = d.get("sent_idx", 0)
            pub_date = d.get("date", "")

            # Tạo event_id duy nhất
            evt_id = assertion_id(doc_id, sent_idx, rel, src, dst, trig)
            if evt_id in seen_events:
                continue
            seen_events.add(evt_id)

            ev_date = explicit_event_date(sent) or pub_date

            # Trích xuất tham số chi tiết bằng event_extractor
            args = extract_event_arguments(
                sentence=sent,
                event_type=rel,
                trigger=trig,
                agent_text=d.get("src_text", ""),
                target_text=d.get("dst_text", "")
            )

            # Node Event
            event_node = {
                "id": evt_id,
                "label": "Event",
                "event_type": rel,
                "trigger": trig,
                "action_content": args.get("action_content", ""),
                "role": args.get("role", ""),
                "appoint_type": args.get("appoint_type", ""),
                "tenure": args.get("tenure", ""),
                "legal_doc": args.get("legal_doc", ""),
                "deadline": args.get("deadline", ""),
                "urgency": args.get("urgency", ""),
                "penalty_form": args.get("penalty_form", ""),
                "violation_reason": args.get("violation_reason", ""),
                "subject_matter": args.get("subject_matter", ""),
                "event_date": ev_date,
                "date": pub_date,
                "evidence": sent[:300],
                "url": d.get("url", "")
            }
            nodes_event.append(event_node)

            # Edge 1: Agent -> Event
            agent_label = d.get("src_label", "Person")
            edges_event.append({
                "src": src,
                "src_label": agent_label,
                "rel": f"CHU_TRI_{rel}" if rel in ("CHU_TRI", "CHI_DAO") else f"KHOI_TAO_{rel}",
                "dst": evt_id,
                "dst_label": "Event",
                "weight": 1.0,
                "event_type": rel
            })

            # Edge 2: Event -> Target
            target_label = d.get("dst_label", "Organization")
            edges_event.append({
                "src": evt_id,
                "src_label": "Event",
                "rel": f"HUONG_TOI_{rel}",
                "dst": dst,
                "dst_label": target_label,
                "weight": 1.0,
                "event_type": rel
            })

    # Ghi file CSV
    node_file = GRAPH_DIR / "nodes_event.csv"
    node_fields = list(nodes_event[0].keys()) if nodes_event else []
    with open(node_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=node_fields)
        writer.writeheader()
        writer.writerows(nodes_event)

    edge_file = GRAPH_DIR / "edges_event.csv"
    edge_fields = list(edges_event[0].keys()) if edges_event else []
    with open(edge_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=edge_fields)
        writer.writeheader()
        writer.writerows(edges_event)

    print(f"Generated {len(nodes_event)} Event nodes -> {node_file}")
    print(f"Generated {len(edges_event)} Event edges -> {edge_file}")
    return len(nodes_event), len(edges_event)


if __name__ == "__main__":
    generate_event_nodes_and_edges()

