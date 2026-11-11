import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "extraction"))

from extraction.vigov_ie_engine import ViGovIEEngine
from extraction.event_extractor import extract_event_arguments

with open('data/eval/event_benchmark_expanded_gold.jsonl', encoding='utf-8') as f:
    records = [json.loads(line) for line in f]

engine = ViGovIEEngine()

count = 0
for r in records:
    g = r.get('gold_arguments', {}).get('role')
    if g:
        v = engine.extract(r['sentence'], r['gold_event_type']).get('role', '')
        b = extract_event_arguments(r['sentence'], r['gold_event_type'], r.get('gold_trigger', '')).get('role', '')
        if b and not v:
            count += 1
            print(f"[{count}] SENT: {r['sentence']}")
            print(f"    GOLD: {g}")
            print(f"    BASE: {b}")
            print(f"    VIGOV: {v}\n")
