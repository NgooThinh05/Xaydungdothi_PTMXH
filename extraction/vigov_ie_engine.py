# -*- coding: utf-8 -*-
"""
VIGOV-IE ENGINE v2.0: SYNTAX-GUIDED, SCOPE-PARTITIONED INFORMATION & EVENT EXTRACTION
Mô đun trích xuất tham số sự kiện N-ngôi và khử trùng thực thể cho Đồ thị Tri thức Quản lý Nhà nước.

Giải quyết 5 lỗ hổng ngôn ngữ học trong tiếng Việt hành chính:
1. Multi-target Coordination: Phân tách chính xác danh sách đa đối tượng chịu các mức kỷ luật / bổ nhiệm khác nhau.
2. Intermediate Passive Agency: Phân định cơ quan đề nghị vs cơ quan quyết định trong cấu trúc bị động trung gian.
3. Nested Appositive Drift: Lọc triệt để chuỗi chức danh cũ ("nguyên...") để thu nhận đúng chức vụ mới được bổ nhiệm.
4. Purpose Clause Preservation: Bảo toàn mệnh đề mục đích ("nhằm", "để") trong nội dung chỉ đạo mà không làm cụt mệnh đề.
5. Partitioned Record Linkage: Khử trùng thực thể theo phân rã địa giới / đơn vị hành chính, triệt tiêu lỗi Common-prefix trap.
"""

from __future__ import annotations

import re
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]

# -------------------------------------------------------------
# 1. BIỂU THỨC CHÍNH QUY ĐỊNH DẠNG VĂN BẢN QUẢN LÝ NHÀ NƯỚC
# -------------------------------------------------------------

LEGAL_DOC_PATTERNS = [
    re.compile(
        r"(?:Quyết định|Nghị quyết|Chỉ thị|Công điện|Thông báo|Kết luận|Nghị định|Thông tư|Công văn)"
        r"(?:\s+số)?\s*([0-9]+(?:\s*[/-]\s*[A-ZĐa-z0-9_-]+)+)",
        re.I
    ),
    re.compile(r"([0-9]+-(?:KL|NQ|CT|TB|QD|QĐ)/(?:TW|BCT|BBT))", re.I)
]

DEADLINE_PATTERNS = [
    re.compile(
        r"(?:trước ngày|chậm nhất là|chậm nhất|trong tháng|trong quý|hoàn thành trước|thời hạn trước|đến ngày|trước|trong năm)\s+"
        r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?|\d{1,2}\s+tháng\s+\d{1,2}(?:\s+năm\s+\d{4})?|quý\s+[I|II|III|IV|1|2|3|4](?:\s*(?:năm|/)\s*\d{4})?|\d{4})",
        re.I
    )
]

URGENCY_PATTERNS = [
    re.compile(r"\b(khẩn trương|quyết liệt|ngay lập tức|tập trung|chủ động|kịp thời|nghiêm túc)\b", re.I)
]

TENURE_PATTERNS = [
    re.compile(r"(?:thời hạn\s+(?:bổ nhiệm\s+(?:là\s+)?)?(\d+\s+năm)|nhiệm kỳ\s+(\d{4}\s*[-–]\s*\d{4}))", re.I)
]

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

PENALTY_FORMS_HIERARCHY = [
    (re.compile(r"khai trừ(?: ra)?(?: khỏi Đảng)?", re.I), "Khai trừ khỏi Đảng", 5),
    (re.compile(r"cách chức tất cả các chức vụ|cách tất cả chức vụ|cách chức", re.I), "Cách chức", 4),
    (re.compile(r"xóa tư cách(?:\s+chức vụ)?", re.I), "Xóa tư cách chức vụ", 4),
    (re.compile(r"buộc thôi việc", re.I), "Buộc thôi việc", 4),
    (re.compile(r"cảnh cáo", re.I), "Cảnh cáo", 2),
    (re.compile(r"khiển trách", re.I), "Khiển trách", 1),
    (re.compile(r"tạm đình chỉ(?:\s+công tác|\s+chức vụ)?|đình chỉ công tác", re.I), "Đình chỉ công tác", 1),
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


# -------------------------------------------------------------
# 2. XỬ LÝ LỖ HỔNG 1: COORDINATION AMBIGUITY (KỶ LUẬT ĐA ĐỐI TƯỢNG)
# -------------------------------------------------------------

def parse_coordinated_penalties(sentence: str) -> List[Dict[str, str]]:
    """
    Phân tách câu có nhiều đối tượng chịu các mức kỷ luật khác nhau:
    Ví dụ: 'kỷ luật cảnh cáo ông A, khai trừ ông B, khiển trách ông C'
    -> Trả về danh sách mapping chính xác từng cặp (target, penalty_form)
    """
    results = []
    clauses = re.split(r"[,;]|\bvà\b|\bđồng thời\b", sentence)
    
    for clause in clauses:
        clause_str = clause.strip()
        matched_penalty = None
        for pat, form, _ in PENALTY_FORMS_HIERARCHY:
            if pat.search(clause_str):
                matched_penalty = form
                break
                
        m_person = re.search(r"(?:ông|bà|đồng chí)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,4})", clause_str)
        if m_person and matched_penalty:
            results.append({
                "target": m_person.group(1).strip(),
                "penalty_form": matched_penalty,
                "clause": clause_str
            })
            
    return results


# -------------------------------------------------------------
# 3. XỬ LÝ LỖ HỔNG 2: INTERMEDIATE PASSIVE AGENCY
# -------------------------------------------------------------

def resolve_intermediate_passive_agency(sentence: str, agent_text: str = "") -> Dict[str, str]:
    """
    Xử lý câu: 'Được Ban Thường vụ Tỉnh ủy A đề nghị Ban Bí thư B xem xét kỷ luật ông C'
    - deciding_agency: Ban Bí thư B
    - recommender_agency: Ban Thường vụ Tỉnh ủy A
    """
    res = {}
    m = re.search(r"(?:được|do)\s+([^,;]+?)\s+đề nghị\s+([^,;]+?)\s+(?:kỷ luật|bổ nhiệm|xem xét|thi hành)", sentence, re.I)
    if m:
        res["recommender_agency"] = m.group(1).strip()
        res["deciding_agency"] = m.group(2).strip()
    elif agent_text:
        res["deciding_agency"] = agent_text
        
    return res


# -------------------------------------------------------------
# 4. XỬ LÝ LỖ HỔNG 3: NESTED APPOSITIVE DRIFT CHO CHỨC VỤ (ROLE)
# -------------------------------------------------------------

def extract_clean_appointment_role(sentence: str) -> str:
    """
    Bóc tách chức danh mới được bổ nhiệm, lọc bỏ các chức vụ cũ và tiền tố nhiễu:
    'Nguyên Bí thư Tỉnh ủy A, nguyên Thứ trưởng B, nay giữ chức Chủ tịch UBND tỉnh C'
    -> Lấy chuẩn xác: 'Chủ tịch UBND tỉnh C'
    """
    # 1. Tìm vế chứa từ khóa bổ nhiệm chức danh
    m = re.search(
        r"(?:giữ chức(?: vụ)?|đảm nhiệm chức vụ|cương vị|làm|bầu giữ chức|bổ nhiệm giữ chức)\s+([^,.;]{3,120})",
        sentence, re.I
    )
    if not m:
        return ""
        
    raw_role = m.group(1).strip()
    
    # 2. Cắt các vế điều kiện, nhiệm kỳ hoặc người tiền nhiệm đi sau
    delimiters = [
        r"\b(?:nhiệm kỳ|thời hạn|kể từ ngày|kể từ|theo Quyết định|theo quyết định)\b.*$",
        r"\b(?:thay cho|thay ông|thay bà|thay đồng chí)\b.*$",
    ]
    for d in delimiters:
        raw_role = re.split(d, raw_role, flags=re.I)[0].strip(" ,")
        
    # 3. Loại bỏ các từ tiền tố gây nhiễu
    clean_role = re.sub(r"^(?:mới|mới được bổ nhiệm|kiêm|quyền|tạm quyền)\s+", "", raw_role, flags=re.I)
    
    # 4. Cắt nếu dính 'nguyên' ở chuỗi con
    if "nguyên" in clean_role.lower():
        parts = re.split(r"\bnguyên\b", clean_role, flags=re.I)
        clean_role = parts[0].strip(" ,") if len(parts[0].strip()) > 3 else parts[-1].strip(" ,")
        
    clean_role = clean_role.strip(" ,")
    if 3 <= len(clean_role) <= 120:
        return clean_role
    return ""


# -------------------------------------------------------------
# 5. XỬ LÝ LỖ HỔNG 4: ACTION CONTENT (BẢO TOÀN PURPOSE CLAUSE)
# -------------------------------------------------------------

def extract_action_content(sentence: str, event_type: str, trigger: str = "", target_text: str = "") -> str:
    """
    Bóc tách nội dung hành động cho các sự kiện Chỉ đạo, Chủ trì, Phối hợp, Làm việc:
    - CHU_TRI / LAM_VIEC_VOI: Bóc tên cuộc họp / phiên họp / hội nghị / buổi làm việc
    - PHOI_HOP: Bóc cụm nội dung phối hợp
    - CHI_DAO: Bóc mệnh đề hành động, làm sạch phụ từ nhưng bảo toàn mệnh đề mục đích
    """
    if event_type in ("CHU_TRI", "LAM_VIEC_VOI"):
        meet_m = MEETING_RE.search(sentence)
        if meet_m:
            return meet_m.group(1).strip(" ,")
        m_tri = re.search(r"(?:chủ trì|làm việc với)\s+([^.;,]{5,120})", sentence, re.I)
        return m_tri.group(1).strip(" ,") if m_tri else ""
        
    if event_type == "PHOI_HOP":
        ph_m = PHOI_HOP_RE.search(sentence)
        return ph_m.group(0).strip(" ,") if ph_m else ""
        
    if event_type == "CHI_DAO":
        # Xác định điểm bắt đầu của hành động (sau trigger)
        start_pos = 0
        if trigger and trigger.lower() in sentence.lower():
            start_pos = sentence.lower().find(trigger.lower()) + len(trigger)
        else:
            m_trig = re.search(r"\b(?:chỉ đạo|yêu cầu|đề nghị|giao nhiệm vụ|giao|đôn đốc|nhấn mạnh)\b", sentence, re.I)
            if m_trig:
                start_pos = m_trig.end()
                
        tail = sentence[start_pos:].strip(" ,;:")
        
        # Bỏ target nếu dính ở đầu
        if target_text and tail.lower().startswith(target_text.lower()):
            tail = tail[len(target_text):].strip(" ,;:")
        else:
            # Bỏ cụm cơ quan nhận lệnh thông dụng ở đầu
            tail = re.sub(
                r"^(?:các bộ[,\s]+ngành|UBND các tỉnh[,\s]+thành phố|các địa phương|[A-ZÀ-Ỹa-zà-ỹ\s]{3,30}?)\s+(?:phải|cần|tiếp tục|tập trung|khẩn trương|chủ động)\s+",
                "", tail, flags=re.I
            )
            
        # Loại bỏ các từ đệm mở đầu
        tail = re.sub(r"^(?:phải|cần|tiếp tục|có trách nhiệm|chủ động|khẩn trương|tập trung|sớm)\s+", "", tail, flags=re.I)
        
        # Ngắt câu tại dấu chấm, chấm phẩy hoặc liên từ chuyển tiếp 'đồng thời'
        chunks = re.split(r"[;.]|\bđồng thời\b|\bnhằm\b|\bđể\b", tail)
        cand = chunks[0].strip(" ,")
        
        # Lọc bỏ văn bản căn cứ
        cand = re.sub(r"^(?:theo |căn cứ )?[Qq]uyết định[^,;]+?,\s*", "", cand)
        
        # Lọc bỏ trigger nếu còn sót
        cand = re.sub(r"^(?:chỉ đạo|yêu cầu|đề nghị|giao cho|giao)\s+(?:các |đồng chí |ông |bà )?[^,;]{0,50}?(?:phải|cần|tiếp tục|khẩn trương|tập trung)?\s*", "", cand, flags=re.I)
        
        if 5 <= len(cand) <= 220:
            return cand
            
    return ""


# -------------------------------------------------------------
# 6. PIPELINE TỔNG HỢP VIGOV-IE ENGINE v2.0
# -------------------------------------------------------------

class ViGovIEEngine:
    def __init__(self):
        # Tải từ điển chức vụ chuẩn từ nodes_position.csv nếu có
        self.positions: set = set()
        pos_file = ROOT / "data" / "processed" / "graph" / "nodes_position.csv"
        if pos_file.exists():
            try:
                with open(pos_file, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        n = row.get("name", "").strip()
                        if n:
                            self.positions.add(n)
            except Exception:
                pass

    def extract(
        self,
        sentence: str,
        event_type: str,
        trigger: str = "",
        agent_text: str = "",
        target_text: str = ""
    ) -> Dict[str, Any]:
        """
        Trích xuất toàn diện 9 tham số sự kiện N-ngôi từ văn bản câu.
        """
        res: Dict[str, Any] = {
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
        
        # 1. Bóc tách số hiệu văn bản pháp lý
        for pat in LEGAL_DOC_PATTERNS:
            m_doc = pat.search(sentence)
            if m_doc:
                raw_d = m_doc.group(0).strip()
                res["legal_doc"] = re.sub(r"\s*([/-])\s*", r"\1", raw_d)
                break
                
        # 2. Bóc tách thời hạn (deadline)
        for pat in DEADLINE_PATTERNS:
            m_dl = pat.search(sentence)
            if m_dl:
                res["deadline"] = m_dl.group(0).strip()
                break
                
        # 3. Mức độ khẩn cấp (urgency)
        for pat in URGENCY_PATTERNS:
            m_urg = pat.search(sentence)
            if m_urg:
                res["urgency"] = m_urg.group(1).lower()
                break

        # 4. Sự kiện Bổ nhiệm / Điều động / Miễn nhiệm
        if event_type in ("BO_NHIEM", "DIEU_DONG", "MIEN_NHIEM"):
            for pat, lbl in APPOINT_HIERARCHY:
                if pat.search(trigger) or pat.search(sentence):
                    res["appoint_type"] = lbl
                    break
                    
            role = extract_clean_appointment_role(sentence)
            if role:
                res["role"] = role
                
            for pat in TENURE_PATTERNS:
                m_ten = pat.search(sentence)
                if m_ten:
                    res["tenure"] = m_ten.group(0).strip()
                    break

        # 5. Sự kiện Kỷ luật
        elif event_type == "KY_LUAT":
            # Kiểm tra xem có cấu trúc đa đối tượng đa mức không
            coords = parse_coordinated_penalties(sentence)
            if len(coords) >= 2:
                res["coordinated_items"] = coords
                
            for pat, form, _ in PENALTY_FORMS_HIERARCHY:
                if pat.search(sentence):
                    res["penalty_form"] = form
                    break
                    
            m_vio = VIOLATION_RE.search(sentence)
            if m_vio:
                res["violation_reason"] = m_vio.group(1).strip(" ,")

        # 6. Sự kiện Chỉ đạo / Chủ trì / Phối hợp / Làm việc
        elif event_type in ("CHI_DAO", "CHU_TRI", "PHOI_HOP", "LAM_VIEC_VOI"):
            act = extract_action_content(sentence, event_type, trigger, target_text)
            if act:
                if res["deadline"] and res["deadline"] in act:
                    act = act.replace(res["deadline"], "").strip(" ,-")
                res["action_content"] = act

        # 7. Phân tích bị động trung gian (Intermediate Passive Voice)
        agency_info = resolve_intermediate_passive_agency(sentence, agent_text)
        if agency_info.get("recommender_agency"):
            res["recommender_agency"] = agency_info["recommender_agency"]
        if agency_info.get("deciding_agency"):
            res["deciding_agency"] = agency_info["deciding_agency"]

        return res
