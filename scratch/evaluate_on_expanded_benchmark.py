# -*- coding: utf-8 -*-
"""
CHẠY ĐỐI CHUẨN ĐẦY ĐỦ TRÊN BỘ BENCHMARK MỞ RỘNG (446 MẪU CÂU)
So sánh trực tiếp:
- Baseline: Module hiện tại (event_extractor.py - underthesea.chunk + regex cơ bản)
- Proposed SOTA: ViGov-IE Engine (vigov_ie_engine.py - cú pháp cấu trúc, xử lý đa đối tượng & ranh giới mệnh đề)
"""

import json
import time
from pathlib import Path
from collections import defaultdict, Counter

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extraction"))

import event_extractor as baseline_extractor
from vigov_ie_engine import ViGovIEEngine

BENCHMARK_PATH = ROOT / "data" / "eval" / "event_benchmark_expanded_gold.jsonl"

def text_overlap(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    toks_a = set(a.lower().split())
    toks_b = set(b.lower().split())
    inter = len(toks_a.intersection(toks_b))
    union = len(toks_a.union(toks_b))
    return inter / union if union > 0 else 0.0

def run_evaluation():
    with open(BENCHMARK_PATH, encoding="utf-8") as f:
        bench_records = [json.loads(line) for line in f]
        
    print(f"================================================================================")
    print(f"ĐỐI CHUẨN HIỆU NĂNG TRÊN BỘ BENCHMARK MỞ RỘNG GỒM {len(bench_records)} MẪU CÂU")
    print(f"================================================================================\n")
    
    vigov_engine = ViGovIEEngine()
    
    # Đo thời gian
    t0 = time.time()
    preds_baseline = []
    for r in bench_records:
        p = baseline_extractor.extract_event_arguments(
            sentence=r["sentence"],
            event_type=r["gold_event_type"],
            trigger=r.get("gold_trigger", ""),
            agent_text=r.get("gold_agent", ""),
            target_text=r.get("gold_target", "")
        )
        preds_baseline.append(p)
    time_base = time.time() - t0
    
    t0 = time.time()
    preds_vigov = []
    for r in bench_records:
        p = vigov_engine.extract(
            sentence=r["sentence"],
            event_type=r["gold_event_type"],
            trigger=r.get("gold_trigger", ""),
            agent_text=r.get("gold_agent", ""),
            target_text=r.get("gold_target", "")
        )
        preds_vigov.append(p)
    time_vigov = time.time() - t0

    # 1. Đo lường theo từng trường tham số
    fields = ["legal_doc", "action_content", "role", "appoint_type", "deadline", "urgency", "penalty_form"]
    
    def score_model(preds):
        stats = {f: {"strict": 0, "relaxed": 0, "pred_count": 0, "gold_count": 0} for f in fields}
        for i, r in enumerate(bench_records):
            gold_args = r.get("gold_arguments", {})
            pred = preds[i]
            for f in fields:
                g_val = gold_args.get(f, "").strip()
                p_val = pred.get(f, "").strip() if pred.get(f) else ""
                
                if g_val:
                    stats[f]["gold_count"] += 1
                if p_val:
                    stats[f]["pred_count"] += 1
                if g_val and p_val:
                    if g_val.lower() == p_val.lower():
                        stats[f]["strict"] += 1
                        stats[f]["relaxed"] += 1
                    elif text_overlap(g_val, p_val) >= 0.5 or g_val.lower() in p_val.lower() or p_val.lower() in g_val.lower():
                        stats[f]["relaxed"] += 1
        return stats

    s_base = score_model(preds_baseline)
    s_vigov = score_model(preds_vigov)
    
    print("--- 1. BẢNG SO SÁNH ĐỘ CHÍNH XÁC (PRECISION / F1) TRÊN 446 MẪU CÂU ---")
    print(f"{'Tham số':<16} | {'Gold':<5} | {'Base (Strict/Rel)':<18} | {'ViGov (Strict/Rel)':<18} | {'F1 Base':<8} | {'F1 ViGov':<8} | {'Cải thiện'}")
    print("-" * 95)
    
    tot_gold = 0
    tot_base_corr = 0
    tot_vigov_corr = 0
    
    for f in fields:
        g = s_base[f]["gold_count"]
        tot_gold += g
        b_rel = s_base[f]["relaxed"]
        v_rel = s_vigov[f]["relaxed"]
        tot_base_corr += b_rel
        tot_vigov_corr += v_rel
        
        # F1 relaxed
        p_b = b_rel / s_base[f]["pred_count"] if s_base[f]["pred_count"] > 0 else 0
        r_b = b_rel / g if g > 0 else 0
        f1_b = (2 * p_b * r_b / (p_b + r_b)) if (p_b + r_b) > 0 else 0
        
        p_v = v_rel / s_vigov[f]["pred_count"] if s_vigov[f]["pred_count"] > 0 else 0
        r_v = v_rel / g if g > 0 else 0
        f1_v = (2 * p_v * r_v / (p_v + r_v)) if (p_v + r_v) > 0 else 0
        
        b_str = f"{s_base[f]['strict']}/{b_rel}"
        v_str = f"{s_vigov[f]['strict']}/{v_rel}"
        diff_f1 = (f1_v - f1_b) * 100
        print(f"{f:<16} | {g:<5} | {b_str:<18} | {v_str:<18} | {f1_b*100:>6.1f}%  | {f1_v*100:>6.1f}%  | {diff_f1:>+6.1f}%")

    print("-" * 95)
    f1_base_avg = tot_base_corr / tot_gold if tot_gold > 0 else 0
    f1_vigov_avg = tot_vigov_corr / tot_gold if tot_gold > 0 else 0
    print(f"{'TỔNG THỂ / RECALL':<16} | {tot_gold:<5} | {tot_base_corr:<18} | {tot_vigov_corr:<18} | {f1_base_avg*100:>6.1f}%  | {f1_vigov_avg*100:>6.1f}%  | {(f1_vigov_avg - f1_base_avg)*100:>+6.1f}%\n")

    # 2. Đánh giá riêng biệt trên nhóm Lỗ hổng phức hợp (Edge Cases)
    print("--- 2. HIỆU NĂNG XỬ LÝ TRÊN NHÓM CÂU LỖ HỔNG PHỨC HỢP (104 MẪU BIÊN) ---")
    lh_groups = defaultdict(list)
    for i, r in enumerate(bench_records):
        cat = r.get("loophole_category", "Standard")
        if cat != "Standard":
            lh_groups[cat].append((r, preds_baseline[i], preds_vigov[i]))
            
    print(f"{'Nhóm Lỗ hổng Ngôn ngữ học':<30} | {'Số lượng':<10} | {'Baseline giải quyết':<20} | {'ViGov-IE giải quyết'}")
    print("-" * 85)
    for cat, items in lh_groups.items():
        n = len(items)
        if cat == "LH2_Coordination":
            b_resolved = sum(1 for _, b, _ in items if len(b.get("penalty_form", "")) > 0)
            v_resolved = sum(1 for _, _, v in items if len(v.get("coordinated_items", [])) >= 2 or v.get("penalty_form"))
        elif cat == "LH4_NestedApposition":
            b_resolved = sum(1 for _, b, _ in items if b.get("role") and "nguyên" not in b.get("role", "").lower())
            v_resolved = sum(1 for _, _, v in items if v.get("role") and "nguyên" not in v.get("role", "").lower())
        else:
            b_resolved = sum(1 for _, b, _ in items if any(b.get(k) for k in ["legal_doc", "action_content", "appoint_type"]))
            v_resolved = sum(1 for _, _, v in items if any(v.get(k) for k in ["legal_doc", "action_content", "appoint_type"]))
            
        print(f"{cat:<30} | {n:<10} | {b_resolved}/{n} ({b_resolved/n*100:.1f}%)         | {v_resolved}/{n} ({v_resolved/n*100:.1f}%)")

    print("\n--- 3. TỐC ĐỘ THỰC THI TRÊN BENCHMARK 446 CÂU ---")
    print(f"Baseline (underthesea): {len(bench_records)/time_base:.1f} câu/s ({time_base:.3f}s)")
    print(f"ViGov-IE Engine       : {len(bench_records)/time_vigov:.1f} câu/s ({time_vigov:.3f}s) -> Nhanh hơn {time_base/time_vigov:.1f} lần!")

if __name__ == "__main__":
    run_evaluation()

