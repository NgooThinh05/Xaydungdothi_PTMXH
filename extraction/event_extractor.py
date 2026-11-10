# -*- coding: utf-8 -*-
"""
Module trích xuất sự kiện chi tiết (Event Extraction & Argument Labeling).
Bổ sung các tham số sự kiện cho Đồ thị Tri thức:
- CHI_DAO: action_content (chỉ đạo làm gì), deadline (thời hạn), urgency (mức độ khẩn)
- BO_NHIEM / DIEU_DONG: role (chức vụ), appoint_type (bổ nhiệm như thế nào), tenure (nhiệm kỳ), legal_doc (số quyết định)
- KY_LUAT: penalty_form (hình thức kỷ luật), violation_reason (lý do/hành vi vi phạm)
- THANH_TRA / KIEM_TRA: subject_matter (nội dung thanh tra, kiểm tra)
- CHU_TRI: meeting_name (tên cuộc họp/hội nghị)

Sử dụng kết hợp:
1. Thư viện underthesea (Chunking & POS Tagging) để xác định ranh giới cụm động từ (B-VP), cụm giới từ (B-PP).
2. Quy tắc cú pháp chuyên sâu (Syntactic Rules & Regex) cho văn bản hành chính Việt Nam.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

try:
    import underthesea
    HAS_UNDERTHESEA = True
except ImportError:
    HAS_UNDERTHESEA = False

# Regex bóc tách số hiệu văn bản pháp lý
LEGAL_DOC_RE = re.compile(
    r"(?:[Qq]uyết định|[Nn]ghị quyết|[Cc]hỉ thị|[Cc]ông điện|[Tt]hông báo|[Kk]ết luận)"
    r"(?:\s+số)?\s+([0-9]+/[A-ZĐa-z0-9_-]+(?:\s*-\s*[A-ZĐa-z0-9]+)?)",
    re.I
)

# Regex bóc tách thời hạn (deadline)
DEADLINE_RE = re.compile(
    r"(?:trước ngày|chậm nhất là|chậm nhất|trong tháng|trong quý|hoàn thành trước|trước)\s+"
    r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?|\d{1,2}\s+tháng\s+\d{1,2}(?:\s+năm\s+\d{4})?|quý\s+[I|II|III|IV](?:\s+năm\s+\d{4})?|\d{4})",
    re.I
)

# Mức độ khẩn cấp
URGENCY_RE = re.compile(r"\b(khẩn trương|quyết liệt|ngay lập tức|tập trung|chủ động|kịp thời|nghiêm túc)\b", re.I)

# Thời hạn / Nhiệm kỳ bổ nhiệm
TENURE_RE = re.compile(
    r"(?:thời hạn\s+(?:bổ nhiệm\s+(?:là\s+)?)?(\d+\s+năm)|nhiệm kỳ\s+(\d{4}\s*[-–]\s*\d{4}))",
    re.I
)

# Hình thức bổ nhiệm
APPOINT_TYPES = [
    (re.compile(r"bổ nhiệm lại", re.I), "Bổ nhiệm lại"),
    (re.compile(r"phê chuẩn", re.I), "Phê chuẩn"),
    (re.compile(r"chỉ định", re.I), "Chỉ định"),
    (re.compile(r"chuẩn y", re.I), "Chuẩn y"),
    (re.compile(r"điều động, bổ nhiệm|điều động và bổ nhiệm", re.I), "Điều động và bổ nhiệm"),
    (re.compile(r"điều động", re.I), "Điều động"),
    (re.compile(r"luân chuyển", re.I), "Luân chuyển"),
    (re.compile(r"biệt phái", re.I), "Biệt phái"),
    (re.compile(r"bổ nhiệm", re.I), "Bổ nhiệm mới"),
    (re.compile(r"bãi nhiệm", re.I), "Bãi nhiệm"),
    (re.compile(r"miễn nhiệm", re.I), "Miễn nhiệm"),
    (re.compile(r"cho thôi giữ chức", re.I), "Cho thôi giữ chức vụ"),
]

# Hình thức kỷ luật
PENALTY_FORMS = [
    (re.compile(r"khai trừ(?: ra)?(?: khỏi Đảng)?", re.I), "Khai trừ khỏi Đảng"),
    (re.compile(r"cách chức tất cả các chức vụ|cách chức", re.I), "Cách chức"),
    (re.compile(r"cảnh cáo", re.I), "Cảnh cáo"),
    (re.compile(r"khiển trách", re.I), "Khiển trách"),
]

# Lý do vi phạm kỷ luật
VIOLATION_RE = re.compile(
    r"(?:do|vì|có vi phạm, khuyết điểm trong|vi phạm quy định về|vi phạm quy định của Đảng|vi phạm pháp luật|liên quan đến vụ án)\s+([^.;]+)",
    re.I
)

# Tên cuộc họp / hội nghị (CHU_TRI)
MEETING_RE = re.compile(
    r"(?:chủ trì|chủ trì cuộc|chủ trì phiên|chủ trì buổi)\s+((?:phiên họp|cuộc họp|hội nghị|buổi làm việc|lễ|tọa đàm|hội thảo)[^.;,]{5,100})",
    re.I
)

# Nội dung thanh tra / kiểm tra
INSPECTION_SUBJECT_RE = re.compile(
    r"(?:thanh tra|kiểm tra|giám sát)(?:\s+trách nhiệm của[^.;,]+)?\s+(?:trong việc|về việc|đối với việc|về)\s+([^.;]+)",
    re.I
)


def extract_legal_doc(sentence: str) -> str:
    """Trích xuất số hiệu văn bản pháp lý (Quyết định, Công điện, Chỉ thị...)."""
    m = LEGAL_DOC_RE.search(sentence)
    return m.group(0).strip() if m else ""


def extract_deadline(sentence: str) -> str:
    """Trích xuất thời hạn hoàn thành (deadline)."""
    m = DEADLINE_RE.search(sentence)
    return m.group(0).strip() if m else ""


def extract_urgency(sentence: str) -> str:
    """Trích xuất mức độ khẩn cấp."""
    m = URGENCY_RE.search(sentence)
    return m.group(1).lower() if m else ""


def extract_appointment_details(sentence: str, trigger: str) -> Dict[str, str]:
    """Bóc tách chi tiết hình thức bổ nhiệm, thời hạn và số quyết định."""
    res = {}
    
    # 1. Hình thức bổ nhiệm
    for pat, label in APPOINT_TYPES:
        if pat.search(trigger) or pat.search(sentence):
            res["appoint_type"] = label
            break
            
    # 2. Thời hạn / Nhiệm kỳ
    tenure_m = TENURE_RE.search(sentence)
    if tenure_m:
        res["tenure"] = tenure_m.group(0).strip()
        
    # 3. Số quyết định
    doc = extract_legal_doc(sentence)
    if doc:
        res["legal_doc"] = doc
        
    return res


def extract_disciplinary_details(sentence: str) -> Dict[str, str]:
    """Bóc tách hình thức kỷ luật và lý do vi phạm."""
    res = {}
    for pat, form in PENALTY_FORMS:
        if pat.search(sentence):
            res["penalty_form"] = form
            break
            
    v_m = VIOLATION_RE.search(sentence)
    if v_m:
        res["violation_reason"] = v_m.group(1).strip(" ,")
        
    return res


def extract_directive_action(sentence: str, target_end_pos: int = -1, trigger_pos: int = -1, target_text: str = "") -> Dict[str, str]:
    """
    Bóc tách nội dung hành động của lệnh chỉ đạo ("chỉ đạo làm gì").
    Sử dụng kết hợp chunking của underthesea và phân tách cú pháp mệnh đề.
    """
    res = {}
    
    # Bóc deadline và urgency trước
    deadline = extract_deadline(sentence)
    if deadline:
        res["deadline"] = deadline
        
    urgency = extract_urgency(sentence)
    if urgency:
        res["urgency"] = urgency

    # Xác định vùng text chứa hành động sau target hoặc trigger
    start_pos = 0
    if target_end_pos > 0 and target_end_pos < len(sentence):
        start_pos = target_end_pos
    elif trigger_pos > 0 and trigger_pos < len(sentence):
        start_pos = trigger_pos
        
    tail = sentence[start_pos:].strip(" ,;:")
    if not tail:
        return res
        
    # Loại bỏ các từ đệm mở đầu như: "phải", "cần", "tiếp tục", "tập trung"
    tail_clean = re.sub(r"^(?:phải|cần|tiếp tục|có trách nhiệm|chủ động)\s+", "", tail, flags=re.I)
    
    # Ngắt câu tại dấu ngắt logic: chấm phẩy, dấu chấm, liên từ chỉ mục đích "để...", "đồng thời..."
    chunks = re.split(r"[;.]|\bđồng thời\b|\bnhằm\b|\bđể\b", tail_clean)
    candidate_action = chunks[0].strip(" ,")
    
    # Nếu có underthesea, có thể chuẩn hóa cụm động từ
    if HAS_UNDERTHESEA and len(candidate_action) > 15:
        try:
            tagged_chunks = underthesea.chunk(candidate_action)
            # Gom các cụm VP và NP sau VP đầu tiên
            vp_started = False
            vp_tokens = []
            for token, pos, chunk_tag in tagged_chunks:
                if chunk_tag.startswith("B-VP") or vp_started:
                    vp_started = True
                    # Ngắt nếu gặp PP thời gian (trước ngày...)
                    if chunk_tag.startswith("B-PP") and any(w in token.lower() for w in ["trước", "vào", "ngày"]):
                        break
                    vp_tokens.append(token)
            if vp_tokens:
                reconstructed = " ".join(vp_tokens).strip(" ,")
                if len(reconstructed) >= 10:
                    candidate_action = reconstructed
        except Exception:
            pass

    # Lọc bỏ phần deadline nếu nó dính ở đuôi
    if deadline and deadline in candidate_action:
        candidate_action = candidate_action.split(deadline)[0].strip(" ,-")

    # Loại bỏ trigger và các từ đầu nếu còn dính
    candidate_action = re.sub(r"^(?:chỉ đạo|yêu cầu|đề nghị|giao cho|giao)\s+(?:các |đồng chí |ông |bà )?[^,;]{0,50}?(?:phải|cần|tiếp tục|khẩn trương|tập trung)?\s*", "", candidate_action, flags=re.I)
    if target_text and candidate_action.lower().startswith(target_text.lower()):
        candidate_action = candidate_action[len(target_text):].strip(" ,")
    candidate_action = candidate_action.strip(" ,")

    if 5 <= len(candidate_action) <= 200:
        res["action_content"] = candidate_action

    return res


def extract_event_arguments(
    sentence: str,
    event_type: str,
    trigger: str,
    agent_text: str = "",
    target_text: str = "",
    target_end_pos: int = -1
) -> Dict[str, Any]:
    """
    Hàm tổng hợp trích xuất toàn bộ các tham số chi tiết của sự kiện.
    """
    args: Dict[str, Any] = {
        "event_type": event_type,
        "trigger": trigger,
        "action_content": "",
        "role": "",
        "appoint_type": "",
        "tenure": "",
        "legal_doc": "",
        "deadline": "",
        "urgency": "",
        "penalty_form": "",
        "violation_reason": "",
        "subject_matter": ""
    }
    
    # 1. Văn bản pháp lý chung
    doc = extract_legal_doc(sentence)
    if doc:
        args["legal_doc"] = doc
        
    # 2. Xử lý chuyên biệt theo từng loại sự kiện
    if event_type == "CHI_DAO":
        act = extract_directive_action(sentence, target_end_pos=target_end_pos, target_text=target_text)
        args.update(act)
        
    elif event_type in ("BO_NHIEM", "DIEU_DONG", "MIEN_NHIEM"):
        app = extract_appointment_details(sentence, trigger)
        args.update(app)
        # Bóc chức vụ nếu có trong câu
        role_m = re.search(r"(?:giữ chức(?: vụ)?|giữ chức danh|làm|bầu giữ chức)\s+([^,.;]{3,80})", sentence)
        if role_m:
            r_str = role_m.group(1).strip()
            # Cắt bỏ phần thời hạn nếu dính kèm
            r_str = re.split(r"\b(?:thời hạn|nhiệm kỳ|kể từ ngày)\b", r_str, flags=re.I)[0].strip(" ,")
            args["role"] = r_str
            
    elif event_type == "KY_LUAT":
        disc = extract_disciplinary_details(sentence)
        args.update(disc)
        
    elif event_type in ("THANH_TRA", "KIEM_TRA"):
        sub_m = INSPECTION_SUBJECT_RE.search(sentence)
        if sub_m:
            args["subject_matter"] = sub_m.group(1).strip(" ,")
        elif "trách nhiệm" in sentence:
            args["subject_matter"] = "thanh tra trách nhiệm thực hiện nhiệm vụ"
            
    elif event_type in ("CHU_TRI", "LAM_VIEC_VOI"):
        meet_m = MEETING_RE.search(sentence)
        if meet_m:
            args["action_content"] = meet_m.group(1).strip(" ,")
            
    elif event_type == "PHOI_HOP":
        # Tìm nội dung phối hợp
        ph_m = re.search(r"phối hợp(?: với[^,.;]+)?\s+(?:tổ chức|triển khai|thực hiện|xây dựng)\s+([^.;,]{5,120})", sentence, re.I)
        if ph_m:
            args["action_content"] = ph_m.group(0).strip(" ,")

    return args
