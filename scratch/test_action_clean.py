import json
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'extraction'))

from scratch.evaluate_on_expanded_benchmark import text_overlap
from extraction.event_extractor import MEETING_RE, DEADLINE_RE

def clean_action(sentence: str, event_type: str, trigger: str = "", target_text: str = "") -> str:
    if event_type in ("CHU_TRI", "LAM_VIEC_VOI"):
        meet_m = MEETING_RE.search(sentence)
        if meet_m:
            return meet_m.group(1).strip(" ,")
        m_tri = re.search(r"(?:chủ trì|làm việc với)\s+([^.;,]{5,120})", sentence, re.I)
        return m_tri.group(1).strip(" ,") if m_tri else ""
        
    if event_type == "PHOI_HOP":
        ph_m = re.search(r"phối hợp(?: với[^,.;]+)?\s+(?:tổ chức|triển khai|thực hiện|xây dựng)\s+([^.;,]{5,120})", sentence, re.I)
        return ph_m.group(0).strip(" ,") if ph_m else ""
        
    if event_type == "CHI_DAO":
        # Find trigger
        start_pos = 0
        if trigger and trigger.lower() in sentence.lower():
            start_pos = sentence.lower().find(trigger.lower()) + len(trigger)
        else:
            m_trig = re.search(r"\b(?:chỉ đạo|yêu cầu|đề nghị|giao nhiệm vụ|giao|đôn đốc|nhấn mạnh)\b", sentence, re.I)
            if m_trig:
                start_pos = m_trig.end()
                
        tail = sentence[start_pos:].strip(" ,;:")
        
        # Advance past target if present
        if target_text and tail.lower().startswith(target_text.lower()):
            tail = tail[len(target_text):].strip(" ,;:")
            
        # Strip common target agency / people titles at start
        tail = re.sub(r"^(?:các bộ[,\s]+ngành|UBND các tỉnh[,\s]+thành phố|các địa phương|Bộ Tư pháp|Bộ Công an|Bộ Quốc phòng|Bộ Tài chính|ông [A-ZÀ-Ỹa-zà-ỹ\s]+|bà [A-ZÀ-Ỹa-zà-ỹ\s]+|đồng chí [A-ZÀ-Ỹa-zà-ỹ\s]+)\s+", "", tail, flags=re.I)
        
        # Strip modal fillers
        tail = re.sub(r"^(?:phải|cần|tiếp tục|có trách nhiệm|chủ động|khẩn trương|tập trung|sớm)\s+", "", tail, flags=re.I)
        
        chunks = re.split(r"[;.]|\bđồng thời\b|\bnhằm\b|\bđể\b", tail)
        cand = chunks[0].strip(" ,")
        
        # Cut deadline
        dl = DEADLINE_RE.search(cand)
        if dl:
            cand = cand.replace(dl.group(0), "").strip(" ,-")
            
        cand = re.sub(r"^(?:theo |căn cứ )?[Qq]uyết định[^,;]+?,\s*", "", cand)
        
        # Final cleanup
        cand = re.sub(r"^(?:chỉ đạo|yêu cầu|đề nghị|giao cho|giao)\s+(?:các |đồng chí |ông |bà )?[^,;]{0,50}?(?:phải|cần|tiếp tục|khẩn trương|tập trung)?\s*", "", cand, flags=re.I)
        
        if 5 <= len(cand) <= 220:
            return cand
            
    return ""

with open(ROOT / 'data/eval/event_benchmark_expanded_gold.jsonl', encoding='utf-8') as f:
    records = [json.loads(line) for line in f]

gold_count = 0
pred_count = 0
strict = 0
relaxed = 0
for r in records:
    g = r.get('gold_arguments', {}).get('action_content', '').strip()
    p = clean_action(r['sentence'], r['gold_event_type'], r.get('gold_trigger', ''), r.get('gold_target', '')).strip()
    if g: gold_count += 1
    if p: pred_count += 1
    if g and p:
        if g.lower() == p.lower():
            strict += 1
            relaxed += 1
        elif text_overlap(g, p) >= 0.5 or g.lower() in p.lower() or p.lower() in g.lower():
            relaxed += 1

p_rel = relaxed / pred_count if pred_count > 0 else 0
r_rel = relaxed / gold_count if gold_count > 0 else 0
f1 = (2 * p_rel * r_rel / (p_rel + r_rel)) if (p_rel + r_rel) > 0 else 0
print(f'Action Clean: Gold={gold_count} | Strict={strict} | Rel={relaxed} | Pred={pred_count} | F1={f1*100:.1f}%')
