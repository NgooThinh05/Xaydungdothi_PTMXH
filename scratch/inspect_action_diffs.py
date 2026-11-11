import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "extraction"))

from extraction.vigov_ie_engine import ViGovIEEngine
from extraction.event_extractor import extract_event_arguments
from scratch.evaluate_on_expanded_benchmark import text_overlap

with open(ROOT / 'data/eval/event_benchmark_expanded_gold.jsonl', encoding='utf-8') as f:
    records = [json.loads(line) for line in f]

engine = ViGovIEEngine()

count = 0
for r in records:
    g = r.get('gold_arguments', {}).get('action_content', '').strip()
    if g:
        v = engine.extract(r['sentence'], r['gold_event_type'], r.get('gold_trigger', ''), r.get('gold_agent', ''), r.get('gold_target', '')).get('action_content', '').strip()
        b = extract_event_arguments(r['sentence'], r['gold_event_type'], r.get('gold_trigger', ''), r.get('gold_agent', ''), r.get('gold_target', '')).get('action_content', '').strip()
        
        # Check strict and overlap
        ov_v = text_overlap(g, v)
        ov_b = text_overlap(g, b)
        
        if ov_b > 0.8 and ov_v < 0.5:
            count += 1
            if count <= 6:
                print(f"[{count}] Event: {r['gold_event_type']} | Trigger: {r.get('gold_trigger')}")
                print(f"  SENT : {r['sentence'][:100]}...")
                print(f"  GOLD : {g}")
                print(f"  BASE : {b}")
                print(f"  VIGOV: {v}")
                print("-" * 50)

print(f"Total cases where Base succeeded and ViGov failed: {count}")
