import json
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "extraction"))

from extraction.event_extractor import (
    LEGAL_DOC_RE, DEADLINE_RE, URGENCY_RE, APPOINT_TYPES,
    MEETING_RE, PENALTY_FORMS, VIOLATION_RE, INSPECTION_SUBJECT_RE
)

# Load positions
positions = set()
with open(ROOT / 'data/processed/graph/nodes_position.csv', encoding='utf-8') as f:
    import csv
    for row in csv.DictReader(f):
        positions.add(row['name'].strip())
        if row.get('hien_thi'):
            positions.add(row['hien_thi'].strip())

print(f"Loaded {len(positions)} position entries.")

def extract_role_v2(sentence: str) -> str:
    # 1. Anchor on key appointment markers
    m = re.search(
        r"(?:giữ chức(?: vụ)?|đảm nhiệm chức vụ|cương vị|làm|bầu giữ chức|bổ nhiệm giữ chức)\s+([^,.;]{3,120})",
        sentence, re.I
    )
    if not m:
        return ""
    
    raw = m.group(1).strip()
    # Delimit on clauses like "nhiệm kỳ", "thời hạn", "thay cho", "thay ông"
    delims = [
        r"\b(?:nhiệm kỳ|thời hạn|kể từ ngày|kể từ|theo Quyết định|theo quyết định)\b.*$",
        r"\b(?:thay cho|thay ông|thay bà|thay đồng chí)\b.*$",
    ]
    for d in delims:
        raw = re.split(d, raw, flags=re.I)[0].strip(" ,")
    
    # Filter noise prefixes
    raw = re.sub(r"^(?:mới|mới được bổ nhiệm|kiêm|quyền|tạm quyền)\s+", "", raw, flags=re.I)
    
    # If contains "nguyên", handle nested appositive
    if "nguyên" in raw.lower():
        parts = re.split(r"\bnguyên\b", raw, flags=re.I)
        raw = parts[0].strip(" ,") if len(parts[0].strip()) > 3 else parts[-1].strip(" ,")
        
    return raw.strip(" ,")

def extract_action_v2(sentence: str, event_type: str, trigger: str = "", target_text: str = "") -> str:
    if event_type in ("CHU_TRI", "LAM_VIEC_VOI"):
        meet_m = MEETING_RE.search(sentence)
        if meet_m:
            return meet_m.group(1).strip(" ,")
        # Fallback
        m_tri = re.search(r"(?:chủ trì|làm việc với)\s+([^.;,]{5,120})", sentence, re.I)
        if m_tri:
            return m_tri.group(1).strip(" ,")
        return ""
        
    if event_type == "PHOI_HOP":
        ph_m = re.search(r"phối hợp(?: với[^,.;]+)?\s+(?:tổ chức|triển khai|thực hiện|xây dựng)\s+([^.;,]{5,120})", sentence, re.I)
        if ph_m:
            return ph_m.group(0).strip(" ,")
        return ""
        
    if event_type == "CHI_DAO":
        # Find trigger
        m_trig = re.search(r"\b(chỉ đạo|yêu cầu|đề nghị|giao nhiệm vụ|giao|đôn đốc|nhấn mạnh)\b", sentence, re.I)
        if not m_trig:
            return ""
        tail = sentence[m_trig.end():].strip(" ,;:")
        
        # Advance past target if present at start
        if target_text and tail.lower().startswith(target_text.lower()):
            tail = tail[len(target_text):].strip(" ,;:")
        else:
            # Strip common target phrases like "các bộ, ngành", "UBND các tỉnh", "Bộ Tài chính"
            tail = re.sub(r"^(?:các bộ[,\s]+ngành|UBND các tỉnh[,\s]+thành phố|các địa phương|[A-ZÀ-Ỹa-zà-ỹ\s]+?)\s+(?:phải|cần|tiếp tục|tập trung|khẩn trương|chủ động)\s+", "", tail, flags=re.I)
            
        # Clean leading modal words
        tail = re.sub(r"^(?:phải|cần|tiếp tục|có trách nhiệm|chủ động|khẩn trương|tập trung|sớm)\s+", "", tail, flags=re.I)
        
        # Split on sentence end or semicolons, but keep purpose clauses unless too long
        clauses = re.split(r"[;.]|\bđồng thời\b", tail)
        cand = clauses[0].strip(" ,")
        
        # Cut deadline if at end
        dl = DEADLINE_RE.search(cand)
        if dl:
            cand = cand.replace(dl.group(0), "").strip(" ,-")
            
        if 8 <= len(cand) <= 250:
            return cand
            
    return ""

def extract_penalty_v2(sentence: str) -> str:
    for pat, form in PENALTY_FORMS:
        if pat.search(sentence):
            return form
    if re.search(r"\bkỷ luật\b", sentence, re.I):
        return "Kỷ luật"
    return ""

