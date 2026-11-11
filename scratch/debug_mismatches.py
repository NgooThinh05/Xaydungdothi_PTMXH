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

print("=== INSPECTING ACTION_CONTENT MISMATCHES ===")
count = 0
for r in records:
    g = r.get('gold_arguments', {}).get('action_content')
    if g:
        v = engine.extract(r['sentence'], r['gold_event_type'])
        v_act = v.get('action_content', '')
        b = extract_event_arguments(r['sentence'], r['gold_event_type'], r.get('gold_trigger', ''))
        b_act = b.get('action_content', '')
        if v_act != g and count < 6:
            count += 1
            sent = r['sentence'][:80]
            print(f"Sentence: {sent}...")
            print(f"  Type : {r['gold_event_type']}")
            print(f"  Gold : {g}")
            print(f"  Base : {b_act}")
            print(f"  ViGov: {v_act}\n")

print("=== INSPECTING ROLE MISMATCHES ===")
count = 0
for r in records:
    g = r.get('gold_arguments', {}).get('role')
    if g:
        v = engine.extract(r['sentence'], r['gold_event_type'])
        v_role = v.get('role', '')
        b = extract_event_arguments(r['sentence'], r['gold_event_type'], r.get('gold_trigger', ''))
        b_role = b.get('role', '')
        if v_role != g and count < 6:
            count += 1
            sent = r['sentence'][:80]
            print(f"Sentence: {sent}...")
            print(f"  Gold : {g}")
            print(f"  Base : {b_role}")
            print(f"  ViGov: {v_role}\n")

print("=== INSPECTING PENALTY_FORM MISMATCHES ===")
count = 0
for r in records:
    g = r.get('gold_arguments', {}).get('penalty_form')
    if g:
        v = engine.extract(r['sentence'], r['gold_event_type'])
        v_p = v.get('penalty_form', '')
        b = extract_event_arguments(r['sentence'], r['gold_event_type'], r.get('gold_trigger', ''))
        b_p = b.get('penalty_form', '')
        if v_p != g and count < 6:
            count += 1
            sent = r['sentence'][:80]
            print(f"Sentence: {sent}...")
            print(f"  Gold : {g}")
            print(f"  Base : {b_p}")
            print(f"  ViGov: {v_p}\n")
