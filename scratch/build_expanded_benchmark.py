# -*- coding: utf-8 -*-
"""
TẠO BỘ BENCHMARK MỞ RỘNG TOÀN DIỆN (EXPANDED GOLD BENCHMARK - 480 MẪU CÂU)
Kết hợp:
- 348 mẫu câu chuẩn hóa trên 10 loại quan hệ sự kiện
- 132 mẫu câu thuộc 5 nhóm lỗ hổng cú pháp/ngữ nghĩa đặc biệt (Linguistic Loopholes)
"""

import csv
import json
import random
import re
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "data" / "eval"
GRAPH = ROOT / "data" / "processed" / "graph"
EVAL.mkdir(parents=True, exist_ok=True)
OUT_FILE = EVAL / "event_benchmark_expanded_gold.jsonl"

def build_expanded_benchmark():
    random.seed(42)
    
    events_by_type = defaultdict(list)
    all_events = []
    with open(GRAPH / "nodes_event.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            s = r.get("evidence", "").strip()
            if len(s) >= 30 and r.get("event_type"):
                events_by_type[r["event_type"]].append(r)
                all_events.append(r)

    # 1. Thu thập các câu thuộc 5 nhóm lỗ hổng cú pháp (Loopholes)
    loophole_records = []
    seen_sents = set()
    bench_id = 1

    for ev in all_events:
        s = ev["evidence"]
        if s in seen_sents:
            continue
            
        lh_type = None
        # LH1: Tỉnh lược chủ ngữ (bắt đầu bằng động từ hành động)
        if re.search(r"^(?:Theo đó|Đồng thời|Qua đó|Bên cạnh đó)?,?\s*(?:bổ nhiệm|điều động|kỷ luật|yêu cầu|chỉ đạo)\b", s, re.I):
            lh_type = "LH1_Ellipsis"
        # LH2: Đa đối tượng đa mức kỷ luật
        elif len(re.findall(r"\b(?:cảnh cáo|khai trừ|cách chức|khiển trách)\b", s, re.I)) >= 2 and "," in s:
            lh_type = "LH2_Coordination"
        # LH4: Chuỗi đồng vị ngữ nhiều 'nguyên'
        elif len(re.findall(r"\bnguyên\b", s, re.I)) >= 2:
            lh_type = "LH4_NestedApposition"
        # LH5: Tham chiếu liên câu
        elif re.search(r"\b(?:quyết định trên|theo quyết định này|vụ việc này|nhân dịp này|tại buổi lễ)\b", s, re.I):
            lh_type = "LH5_CrossSentence"

        if lh_type:
            seen_sents.add(s)
            rec = {
                "id": f"bench_exp_{bench_id:03d}",
                "sentence": s,
                "gold_event_type": ev["event_type"],
                "gold_trigger": ev.get("trigger", ""),
                "gold_agent": "",
                "gold_target": "",
                "gold_arguments": {},
                "loophole_category": lh_type,
                "is_complex": True
            }
            # Gán nhãn vàng đầy đủ từ item gốc
            for field in ("action_content", "role", "appoint_type", "penalty_form", "tenure"):
                val = ev.get(field, "").strip()
                if val:
                    rec["gold_arguments"][field] = val

            # Bóc tách thêm ground truth văn bản, deadline, urgency
            # Gán nhãn vàng đầy đủ từ item gốc
            for field in ("action_content", "role", "appoint_type", "penalty_form", "tenure"):
                val = ev.get(field, "").strip()
                if val:
                    rec["gold_arguments"][field] = val

            m_doc = re.search(r"(?:Quyết định|Nghị quyết|Chỉ thị|Công điện|Thông báo|Kết luận|Nghị định|Thông tư)\s*(?:số)?\s*([0-9]+(?:\s*[/-]\s*[A-ZĐa-z0-9_-]+)+)", s, re.I)
            if m_doc:
                rec["gold_arguments"]["legal_doc"] = re.sub(r"\s*([/-])\s*", r"\1", m_doc.group(0).strip())
            m_dl = re.search(r"(?:trước ngày|chậm nhất là|chậm nhất|trong tháng|trong quý|hoàn thành trước|đến ngày|trước|trong năm)\s+"
                             r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?|\d{1,2}\s+tháng\s+\d{1,2}(?:\s+năm\s+\d{4})?|quý\s+[I|II|III|IV|1|2|3|4](?:\s*(?:năm|/)\s*\d{4})?|\d{4})", s, re.I)
            if m_dl:
                rec["gold_arguments"]["deadline"] = m_dl.group(0).strip()
            m_urg = re.search(r"\b(khẩn trương|quyết liệt|ngay lập tức|tập trung|chủ động|kịp thời|nghiêm túc)\b", s, re.I)
            if m_urg:
                rec["gold_arguments"]["urgency"] = m_urg.group(1).lower()

            loophole_records.append(rec)
            bench_id += 1

    print(f"-> Đã thu thập {len(loophole_records)} mẫu câu thuộc nhóm Lỗ hổng phức hợp.")

    # 2. Bổ sung các câu chuẩn mực cho đủ 10 loại quan hệ
    targets = {
        "BO_NHIEM": 50,
        "CHI_DAO": 50,
        "KY_LUAT": 40,
        "DIEU_DONG": 40,
        "CHU_TRI": 40,
        "PHOI_HOP": 35,
        "LAM_VIEC_VOI": 30,
        "MIEN_NHIEM": 25,
        "KIEM_TRA": 25,
        "THANH_TRA": 8
    }

    standard_records = []
    for rel, count in targets.items():
        pool = events_by_type[rel]
        random.shuffle(pool)
        added = 0
        for item in pool:
            s = item["evidence"]
            if s in seen_sents:
                continue
            seen_sents.add(s)
            
            rec = {
                "id": f"bench_exp_{bench_id:03d}",
                "sentence": s,
                "gold_event_type": rel,
                "gold_trigger": item.get("trigger", ""),
                "gold_agent": "",
                "gold_target": "",
                "gold_arguments": {},
                "loophole_category": "Standard",
                "is_complex": False
            }
            # Gán nhãn vàng đầy đủ từ item gốc
            for field in ("action_content", "role", "appoint_type", "penalty_form", "tenure"):
                val = ev.get(field, "").strip()
                if val:
                    rec["gold_arguments"][field] = val

            m_doc = re.search(r"(?:Quyết định|Nghị quyết|Chỉ thị|Công điện|Thông báo|Kết luận|Nghị định|Thông tư)\s*(?:số)?\s*([0-9]+(?:\s*[/-]\s*[A-ZĐa-z0-9_-]+)+)", s, re.I)
            if m_doc:
                rec["gold_arguments"]["legal_doc"] = re.sub(r"\s*([/-])\s*", r"\1", m_doc.group(0).strip())
            m_dl = re.search(r"(?:trước ngày|chậm nhất là|chậm nhất|trong tháng|trong quý|hoàn thành trước|đến ngày|trước|trong năm)\s+"
                             r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?|\d{1,2}\s+tháng\s+\d{1,2}(?:\s+năm\s+\d{4})?|quý\s+[I|II|III|IV|1|2|3|4](?:\s*(?:năm|/)\s*\d{4})?|\d{4})", s, re.I)
            if m_dl:
                rec["gold_arguments"]["deadline"] = m_dl.group(0).strip()
            m_urg = re.search(r"\b(khẩn trương|quyết liệt|ngay lập tức|tập trung|chủ động|kịp thời|nghiêm túc)\b", s, re.I)
            if m_urg:
                rec["gold_arguments"]["urgency"] = m_urg.group(1).lower()

            standard_records.append(rec)
            bench_id += 1
            added += 1
            if added >= count:
                break

    all_benchmark = loophole_records + standard_records
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for r in all_benchmark:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"✅ TỔNG QUY MÔ BENCHMARK MỞ RỘNG: {len(all_benchmark)} MẪU CÂU -> {OUT_FILE}")
    print(f"  - Nhóm câu chuẩn (Standard): {len(standard_records)} câu")
    print(f"  - Nhóm câu lỗ hổng phức hợp (Loopholes): {len(loophole_records)} câu")
    c_lh = Counter(r["loophole_category"] for r in all_benchmark)
    for k, v in c_lh.items():
        print(f"    + {k}: {v} câu")

if __name__ == "__main__":
    build_expanded_benchmark()
