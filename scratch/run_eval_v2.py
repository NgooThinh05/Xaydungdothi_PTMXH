# -*- coding: utf-8 -*-
import json
import time
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'extraction'))

from scratch.evaluate_v2_full import ViGovIEEngineV2
import event_extractor as baseline_extractor
from scratch.evaluate_on_expanded_benchmark import text_overlap

BENCHMARK_PATH = ROOT / 'data' / 'eval' / 'event_benchmark_expanded_gold.jsonl'
with open(BENCHMARK_PATH, encoding='utf-8') as f:
    bench_records = [json.loads(line) for line in f]

engine = ViGovIEEngineV2()

# 1. Benchmark timing
t0 = time.time()
preds_base = [baseline_extractor.extract_event_arguments(r['sentence'], r['gold_event_type'], r.get('gold_trigger', ''), r.get('gold_agent', ''), r.get('gold_target', '')) for r in bench_records]
t_base = time.time() - t0

t0 = time.time()
preds_vigov2 = [engine.extract(r['sentence'], r['gold_event_type'], r.get('gold_trigger', ''), r.get('gold_agent', ''), r.get('gold_target', '')) for r in bench_records]
t_vigov2 = time.time() - t0

fields = ['legal_doc', 'action_content', 'role', 'appoint_type', 'deadline', 'urgency', 'penalty_form']

def score_model(preds):
    stats = {f: {'strict': 0, 'relaxed': 0, 'pred_count': 0, 'gold_count': 0} for f in fields}
    for i, r in enumerate(bench_records):
        gold_args = r.get('gold_arguments', {})
        pred = preds[i]
        for f in fields:
            g_val = gold_args.get(f, '').strip()
            p_val = pred.get(f, '').strip() if pred.get(f) else ''
            if g_val: stats[f]['gold_count'] += 1
            if p_val: stats[f]['pred_count'] += 1
            if g_val and p_val:
                if g_val.lower() == p_val.lower():
                    stats[f]['strict'] += 1
                    stats[f]['relaxed'] += 1
                elif text_overlap(g_val, p_val) >= 0.5 or g_val.lower() in p_val.lower() or p_val.lower() in g_val.lower():
                    stats[f]['relaxed'] += 1
    return stats

s_base = score_model(preds_base)
s_v2 = score_model(preds_vigov2)

print('=== KẾT QUẢ ĐỐI CHUẨN: BASELINE vs VIGOV-IE V2 (446 CÂU) ===')
header = f"{'Tham số':<16} | {'Gold':<5} | {'Base (Str/Rel)':<16} | {'ViGov v2 (Str/Rel)':<20} | {'F1 Base':<8} | {'F1 ViGov2':<10} | {'Cải thiện'}"
print(header)
print('-' * len(header))

tot_gold = 0
tot_base_corr = 0
tot_v2_corr = 0

for f in fields:
    g = s_base[f]['gold_count']
    tot_gold += g
    b_rel = s_base[f]['relaxed']
    v_rel = s_v2[f]['relaxed']
    tot_base_corr += b_rel
    tot_v2_corr += v_rel
    
    p_b = b_rel / s_base[f]['pred_count'] if s_base[f]['pred_count'] > 0 else 0
    r_b = b_rel / g if g > 0 else 0
    f1_b = (2 * p_b * r_b / (p_b + r_b)) if (p_b + r_b) > 0 else 0
    
    p_v = v_rel / s_v2[f]['pred_count'] if s_v2[f]['pred_count'] > 0 else 0
    r_v = v_rel / g if g > 0 else 0
    f1_v = (2 * p_v * r_v / (p_v + r_v)) if (p_v + r_v) > 0 else 0
    
    b_str = f"{s_base[f]['strict']}/{b_rel}"
    v_str = f"{s_v2[f]['strict']}/{v_rel}"
    diff_f1 = (f1_v - f1_b) * 100
    print(f"{f:<16} | {g:<5} | {b_str:<16} | {v_str:<20} | {f1_b*100:>6.1f}%  | {f1_v*100:>8.1f}%  | {diff_f1:>+7.1f}%")

print('-' * len(header))
f1_base_avg = tot_base_corr / tot_gold if tot_gold > 0 else 0
f1_v2_avg = tot_v2_corr / tot_gold if tot_gold > 0 else 0
print(f"{'TỔNG THỂ / RECALL':<16} | {tot_gold:<5} | {tot_base_corr:<16} | {tot_v2_corr:<20} | {f1_base_avg*100:>6.1f}%  | {f1_v2_avg*100:>8.1f}%  | {(f1_v2_avg - f1_base_avg)*100:>+7.1f}%")

print(f"\nTốc độ Baseline (underthesea): {len(bench_records)/t_base:.1f} câu/s ({t_base:.3f}s)")
print(f"Tốc độ ViGov-IE v2           : {len(bench_records)/t_vigov2:.1f} câu/s ({t_vigov2:.3f}s) -> Nhanh hơn {t_base/t_vigov2:.1f} lần!")
