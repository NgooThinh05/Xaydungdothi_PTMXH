# -*- coding: utf-8 -*-
"""
THỬ NGHIỆM ĐẦY ĐỦ VIGOV-IE V2 TRÊN BỘ BENCHMARK MỞ RỘNG (446 CÂU)
"""

import re
import json
import time
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]

# -------------------------------------------------------------
# 1. BIỂU THỨC CHÍNH QUY NÂNG CAO CHO VĂN BẢN QUẢN LÝ NHÀ NƯỚC
# -------------------------------------------------------------

LEGAL_DOC_PATTERNS = [
    re.compile(
        r"(?:Quyết định|Nghị quyết|Chỉ thị|Công điện|Thông báo|Kết luận|Nghị định|Thông tư|Công văn)"
        r"(?:\s+số)?\s*([0-9]+(?:\s*[/-]\s*[A-ZĐa-z0-9_-]+)+)",
        re.I
    ),
    re.compile(r"([0-9]+-(?:KL|NQ|CT|TB|QD|QĐ)/(?:TW|BCT|BBT))", re.I)
]

DEADLINE_RE = re.compile(
    r"(?:trước ngày|chậm nhất là|chậm nhất|trong tháng|trong quý|hoàn thành trước|thời hạn trước|đến ngày|trước|trong năm)\s+"
    r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?|\d{1,2}\s+tháng\s+\d{1,2}(?:\s+năm\s+\d{4})?|quý\s+[I|II|III|IV|1|2|3|4](?:\s*(?:năm|/)\s*\d{4})?|\d{4})",
    re.I
)

URGENCY_RE = re.compile(r"\b(khẩn trương|quyết liệt|ngay lập tức|tập trung|chủ động|kịp thời|nghiêm túc)\b", re.I)

TENURE_RE = re.compile(
    r"(?:thời hạn\s+(?:bổ nhiệm\s+(?:là\s+)?)?(\d+\s+năm)|nhiệm kỳ\s+(\d{4}\s*[-–]\s*\d{4}))",
    re.I
)

APPOINT_HIERARCHY = [
    (re.compile(r"bổ nhiệm lại", re.I), "Bổ nhiệm lại"),
    (re.compile(r"phê chuẩn(?:\s+kết quả|\s+việc)?", re.I), "Phê chuẩn"),
    (re.compile(r"chỉ định(?: tham gia)?", re.I), "Chỉ định"),
    (re.compile(r"chuẩn y", re.I), "Chuẩn y"),
    (re.compile(r"điều động(?:,| và|\s+)bổ nhiệm", re.I), "Điều động và bổ nhiệm"),
    (re.compile(r"điều động", re.I), "Điều động"),
    (re.compile(r"luân chuyển", re.I), "Luân chuyển"),
    (re.compile(r"biệt phái", re.I), "Biệt phái"),
    (re.compile(r"tạm giao quyền|giao quyền|phụ trách", re.I), "Giao quyền / Phụ trách"),
    (re.compile(r"bổ nhiệm", re.I), "Bổ nhiệm mới"),
    (re.compile(r"bãi nhiệm", re.I), "Bãi nhiệm"),
    (re.compile(r"miễn nhiệm", re.I), "Miễn nhiệm"),
    (re.compile(r"cho thôi giữ chức(?: vụ)?|thôi giữ chức(?: vụ)?", re.I), "Cho thôi giữ chức vụ"),
]

PENALTY_FORMS_V2 = [
    (re.compile(r"khai trừ(?: ra)?(?: khỏi Đảng)?", re.I), "Khai trừ khỏi Đảng"),
    (re.compile(r"cách chức tất cả các chức vụ|cách chức", re.I), "Cách chức"),
    (re.compile(r"xóa tư cách(?:\s+chức vụ)?", re.I), "Xóa tư cách chức vụ"),
    (re.compile(r"buộc thôi việc", re.I), "Buộc thôi việc"),
    (re.compile(r"cảnh cáo", re.I), "Cảnh cáo"),
    (re.compile(r"khiển trách", re.I), "Khiển trách"),
    (re.compile(r"tạm đình chỉ(?:\s+công tác|\s+chức vụ)?|đình chỉ công tác", re.I), "Đình chỉ công tác"),
]

VIOLATION_RE = re.compile(
    r"(?:do|vì|có vi phạm, khuyết điểm trong|vi phạm quy định về|vi phạm quy định của Đảng|vi phạm pháp luật|liên quan đến vụ án)\s+([^.;]+)",
    re.I
)

MEETING_RE = re.compile(
    r"(?:chủ trì|chủ trì cuộc|chủ trì phiên|chủ trì buổi)\s+((?:phiên họp|cuộc họp|hội nghị|buổi làm việc|lễ|tọa đàm|hội thảo)[^.;,]{5,100})",
    re.I
)

PHOI_HOP_RE = re.compile(
    r"phối hợp(?: với[^,.;]+)?\s+(?:tổ chức|triển khai|thực hiện|xây dựng)\s+([^.;,]{5,120})",
    re.I
)

# Tải từ điển chức vụ chuẩn
POSITIONS_DICT = set()
with open(ROOT / "data" / "processed" / "graph" / "nodes_position.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        name = row["name"].strip()
        if name:
            POSITIONS_DICT.add(name)

# -------------------------------------------------------------
# 2. CÁC HÀM TRÍCH XUẤT CẢI TIẾN
# -------------------------------------------------------------

def extract_legal_doc_v2(sentence: str) -> str:
    for pat in LEGAL_DOC_PATTERNS:
        m = pat.search(sentence)
        if m:
            raw = m.group(0).strip()
            return re.sub(r"\s*([/-])\s*", r"\1", raw)
    return ""

def extract_role_v2(sentence: str) -> str:
    m = re.search(
        r"(?:giữ chức(?: vụ)?|đảm nhiệm chức vụ|cương vị|làm|bầu giữ chức|bổ nhiệm giữ chức)\s+([^,.;]{3,120})",
        sentence, re.I
    )
    if not m:
        return ""
    
    raw = m.group(1).strip()
    delims = [
        r"\b(?:nhiệm kỳ|thời hạn|kể từ ngày|kể từ|theo Quyết định|theo quyết định)\b.*$",
        r"\b(?:thay cho|thay ông|thay bà|thay đồng chí)\b.*$",
    ]
    for d in delims:
        raw = re.split(d, raw, flags=re.I)[0].strip(" ,")
    
    raw = re.sub(r"^(?:mới|mới được bổ nhiệm|kiêm|quyền|tạm quyền)\s+", "", raw, flags=re.I)
    
    if "nguyên" in raw.lower():
        parts = re.split(r"\bnguyên\b", raw, flags=re.I)
        raw = parts[0].strip(" ,") if len(parts[0].strip()) > 3 else parts[-1].strip(" ,")
        
    return raw.strip(" ,")

def extract_action_v2(sentence: str, event_type: str, trigger: str = "", target_text: str = "") -> str:
    if event_type in ("CHU_TRI", "LAM_VIEC_VOI"):
        meet_m = MEETING_RE.search(sentence)
        if meet_m:
            return meet_m.group(1).strip(" ,")
        m_tri = re.search(r"(?:chủ trì|làm việc với)\s+([^.;,]{5,120})", sentence, re.I)
        if m_tri:
            return m_tri.group(1).strip(" ,")
        return ""
        
    if event_type == "PHOI_HOP":
        ph_m = PHOI_HOP_RE.search(sentence)
        if ph_m:
            return ph_m.group(0).strip(" ,")
        return ""
        
    if event_type == "CHI_DAO":
        m_trig = re.search(r"\b(chỉ đạo|yêu cầu|đề nghị|giao nhiệm vụ|giao|đôn đốc|nhấn mạnh)\b", sentence, re.I)
        if not m_trig:
            return ""
        tail = sentence[m_trig.end():].strip(" ,;:")
        
        if target_text and tail.lower().startswith(target_text.lower()):
            tail = tail[len(target_text):].strip(" ,;:")
        else:
            tail = re.sub(r"^(?:các bộ[,\s]+ngành|UBND các tỉnh[,\s]+thành phố|các địa phương|[A-ZÀ-Ỹa-zà-ỹ\s]+?)\s+(?:phải|cần|tiếp tục|tập trung|khẩn trương|chủ động)\s+", "", tail, flags=re.I)
            
        tail = re.sub(r"^(?:phải|cần|tiếp tục|có trách nhiệm|chủ động|khẩn trương|tập trung|sớm)\s+", "", tail, flags=re.I)
        
        clauses = re.split(r"[;.]|\bđồng thời\b", tail)
        cand = clauses[0].strip(" ,")
        
        dl = DEADLINE_RE.search(cand)
        if dl:
            cand = cand.replace(dl.group(0), "").strip(" ,-")
            
        cand = re.sub(r"^(?:theo |căn cứ )?[Qq]uyết định[^,;]+?,\s*", "", cand)
        
        if 5 <= len(cand) <= 250:
            return cand
            
    return ""

def extract_penalty_v2(sentence: str) -> str:
    for pat, form in PENALTY_FORMS_V2:
        if pat.search(sentence):
            return form
    return ""

# -------------------------------------------------------------
# 3. CLASS ENGINE HOÀN CHỈNH
# -------------------------------------------------------------

class ViGovIEEngineV2:
    def __init__(self):
        pass

    def extract(self, sentence: str, event_type: str, trigger: str = "", agent_text: str = "", target_text: str = "") -> dict:
        res = {
            "legal_doc": "",
            "action_content": "",
            "role": "",
            "appoint_type": "",
            "deadline": "",
            "urgency": "",
            "penalty_form": "",
            "violation_reason": "",
            "tenure": "",
            "coordinated_items": []
        }
        
        # 1. Văn bản pháp lý chung
        doc = extract_legal_doc_v2(sentence)
        if doc:
            res["legal_doc"] = doc
            
        # 2. Thời hạn (deadline)
        m_dl = DEADLINE_RE.search(sentence)
        if m_dl:
            res["deadline"] = m_dl.group(0).strip()
            
        # 3. Mức độ khẩn
        m_urg = URGENCY_RE.search(sentence)
        if m_urg:
            res["urgency"] = m_urg.group(1).lower()
            
        # 4. Bổ nhiệm / Điều động
        if event_type in ("BO_NHIEM", "DIEU_DONG", "MIEN_NHIEM"):
            for pat, lbl in APPOINT_HIERARCHY:
                if pat.search(trigger) or pat.search(sentence):
                    res["appoint_type"] = lbl
                    break
            role = extract_role_v2(sentence)
            if role:
                res["role"] = role
            m_ten = TENURE_RE.search(sentence)
            if m_ten:
                res["tenure"] = m_ten.group(0).strip()
                
        # 5. Kỷ luật
        elif event_type == "KY_LUAT":
            p = extract_penalty_v2(sentence)
            if p:
                res["penalty_form"] = p
            m_vio = VIOLATION_RE.search(sentence)
            if m_vio:
                res["violation_reason"] = m_vio.group(1).strip(" ,")
                
        # 6. Chỉ đạo / Chủ trì / Phối hợp
        elif event_type in ("CHI_DAO", "CHU_TRI", "PHOI_HOP", "LAM_VIEC_VOI"):
            act = extract_action_v2(sentence, event_type, trigger, target_text)
            if act:
                res["action_content"] = act

        return res

