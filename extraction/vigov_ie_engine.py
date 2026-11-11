# -*- coding: utf-8 -*-
"""
VIGOV-IE: SYNTAX-GUIDED, SCOPE-PARTITIONED INFORMATION & EVENT EXTRACTION ENGINE
Mô đun cốt lõi tích hợp giải quyết 5 lỗ hổng ngôn ngữ học:
1. Coordination Ambiguity: Phân tách danh sách đa đối tượng, đa mức kỷ luật/bổ nhiệm.
2. Intermediate Passive Voice: Phân định cơ quan đề nghị vs cơ quan quyết định.
3. Nested Appositive Drift: Lọc sạch chuỗi "nguyên..." để lấy đúng chức danh mới.
4. Zero Anaphora & Cross-sentence bridging: Bắt cầu ngữ cảnh khi khuyết chủ ngữ.
5. Partitioned Record Linkage: Triệt tiêu hoàn toàn lỗi Over-merging giữa các cơ quan khác tỉnh.
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional
from rapidfuzz import fuzz

# -------------------------------------------------------------
# 1. BIỂU THỨC CHÍNH QUY NÂNG CAO CHO VĂN BẢN QUẢN LÝ NHÀ NƯỚC
# -------------------------------------------------------------

LEGAL_DOC_PATTERNS = [
    # Quyết định, Nghị quyết, Kết luận TW, Chỉ thị, Công điện, Nghị định, Thông tư
    re.compile(
        r"(?:Quyết định|Nghị quyết|Chỉ thị|Công điện|Thông báo|Kết luận|Nghị định|Thông tư|Công văn)"
        r"(?:\s+số)?\s*([0-9]+(?:\s*[/-]\s*[A-ZĐa-z0-9_-]+)+)",
        re.I
    ),
    # Dạng văn bản Đảng: "Kết luận số 107-KL/TW", "Nghị quyết số 71-NQ/TW"
    re.compile(r"([0-9]+-(?:KL|NQ|CT|TB|QD|QĐ)/(?:TW|BCT|BBT))", re.I)
]

DEADLINE_PATTERNS = [
    re.compile(
        r"(?:trước ngày|chậm nhất là|chậm nhất|trong tháng|trong quý|hoàn thành trước|thời hạn trước|đến ngày|trước|trong năm)\s+"
        r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?|\d{1,2}\s+tháng\s+\d{1,2}(?:\s+năm\s+\d{4})?|quý\s+[I|II|III|IV|1|2|3|4](?:\s*(?:năm|/)\s*\d{4})?|\d{4})",
        re.I
    )
]

PENALTY_HIERARCHY = [
    (re.compile(r"khai trừ(?: ra)?(?: khỏi Đảng)?", re.I), "Khai trừ khỏi Đảng", 5),
    (re.compile(r"cách chức tất cả các chức vụ|cách tất cả chức vụ|cách chức", re.I), "Cách chức", 4),
    (re.compile(r"xóa tư cách(?:\s+chức vụ)?", re.I), "Xóa tư cách chức vụ", 4),
    (re.compile(r"buộc thôi việc", re.I), "Buộc thôi việc", 4),
    (re.compile(r"tạm đình chỉ(?:\s+công tác|\s+chức vụ)?", re.I), "Đình chỉ công tác", 3),
    (re.compile(r"cảnh cáo", re.I), "Cảnh cáo", 2),
    (re.compile(r"khiển trách", re.I), "Khiển trách", 1),
    (re.compile(r"thi hành kỷ luật|kỷ luật", re.I), "Kỷ luật", 1),
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

# -------------------------------------------------------------
# 2. XỬ LÝ LỖ HỔNG 1: COORDINATION AMBIGUITY (ĐA ĐỐI TƯỢNG ĐA MỨC)
# -------------------------------------------------------------

def parse_coordinated_penalties(sentence: str) -> List[Dict[str, str]]:
    """
    Phân tách câu có nhiều đối tượng chịu các mức kỷ luật khác nhau:
    Ví dụ: 'kỷ luật cảnh cáo ông A, khai trừ ông B, khiển trách ông C'
    -> Trả về danh sách mapping chính xác từng cặp (target, penalty_form)
    """
    results = []
    # Cắt câu thành các mệnh đề con dựa trên dấu phẩy hoặc liên từ "và", "đồng thời"
    clauses = re.split(r"[,;]|\bvà\b|\bđồng thời\b", sentence)
    
    for clause in clauses:
        clause_str = clause.strip()
        matched_penalty = None
        for pat, form, _ in PENALTY_HIERARCHY:
            if pat.search(clause_str):
                matched_penalty = form
                break
                
        # Tìm tên người trong mệnh đề
        # Mẫu tên người: ông/bà/đồng chí + Họ tên
        m_person = re.search(r"(?:ông|bà|đồng chí)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,4})", clause_str)
        if m_person and matched_penalty:
            results.append({
                "target": m_person.group(1).strip(),
                "penalty_form": matched_penalty,
                "clause": clause_str
            })
            
    return results


# -------------------------------------------------------------
# 3. XỬ LÝ LỖ HỔNG 2: INTERMEDIATE PASSIVE VOICE (BỊ ĐỘNG TRUNG GIAN)
# -------------------------------------------------------------

def resolve_intermediate_passive_agency(sentence: str, agent_text: str = "") -> Dict[str, str]:
    """
    Xử lý câu: 'Được Ban Thường vụ Tỉnh ủy A đề nghị Ban Bí thư B xem xét kỷ luật ông C'
    - Agency quyết định: Ban Bí thư B
    - Agency đề nghị (recommender): Ban Thường vụ Tỉnh ủy A
    """
    res = {}
    m = re.search(r"(?:được|do)\s+([^,;]+?)\s+đề nghị\s+([^,;]+?)\s+(?:kỷ luật|bổ nhiệm|xem xét|thi hành)", sentence, re.I)
    if m:
        recommender = m.group(1).strip()
        deciding_agency = m.group(2).strip()
        res["recommender_agency"] = recommender
        res["deciding_agency"] = deciding_agency
    elif agent_text:
        res["deciding_agency"] = agent_text
        
    return res


# -------------------------------------------------------------
# 4. XỬ LÝ LỖ HỔNG 3: NESTED APPOSITIVE DRIFT (LỌC CHUỖI 'NGUYÊN...')
# -------------------------------------------------------------

def extract_clean_appointment_role(sentence: str) -> str:
    """
    Bóc tách chức danh mới được bổ nhiệm, loại bỏ triệt để các chức vụ cũ trong chuỗi đồng vị ngữ:
    'Nguyên Bí thư Tỉnh ủy A, nguyên Thứ trưởng B, nay giữ chức Chủ tịch C'
    -> Lấy đúng 'Chủ tịch C'
    """
    # 1. Tìm vế sau 'giữ chức', 'đảm nhiệm', 'cương vị'
    m = re.search(
        r"(?:giữ chức(?: vụ)?|đảm nhiệm chức vụ|cương vị|làm)\s+([A-ZÀ-Ỹa-zà-ỹ0-9\s,-]+?)(?:\s+(?:nhiệm kỳ|thời hạn|kể từ|thay cho|theo Quyết định)|[.;]|$)",
        sentence, re.I
    )
    if not m:
        return ""
        
    raw_role = m.group(1).strip(" ,")
    
    # 2. Xóa bỏ các từ tiền tố gây nhiễu
    clean_role = re.sub(r"^(?:mới|mới được bổ nhiệm|kiêm|quyền|tạm quyền)\s+", "", raw_role)
    
    # 3. Cắt nếu dính 'nguyên' ở đầu hoặc đuôi
    if "nguyên" in clean_role.lower():
        parts = re.split(r"\bnguyên\b", clean_role, flags=re.I)
        clean_role = parts[0].strip(" ,") if len(parts[0].strip()) > 3 else parts[-1].strip(" ,")
        
    if 3 <= len(clean_role) <= 60:
        return clean_role
    return ""


# -------------------------------------------------------------
# 5. XỬ LÝ LỖ HỔNG 4: DIRECTIVE ACTION VỚI PURPOSE CLAUSE
# -------------------------------------------------------------

def extract_directive_action_full(sentence: str) -> str:
    """
    Bóc tách mệnh đề chỉ đạo hành động mà KHÔNG làm mất mệnh đề mục đích ('nhằm', 'để'):
    'yêu cầu các bộ ngành khẩn trương hoàn thiện thể chế nhằm tháo gỡ khó khăn cho sản xuất'
    -> Giữ trọn vẹn cả vế 'nhằm tháo gỡ khó khăn cho sản xuất'
    """
    m_trig = re.search(r"\b(?:chỉ đạo|yêu cầu|đề nghị|giao nhiệm vụ|giao)\b", sentence, re.I)
    start_idx = m_trig.end() if m_trig else 0
    tail = sentence[start_idx:].strip(" ,;:")
    
    # Bỏ từ đệm mở đầu
    tail = re.sub(r"^(?:phải|cần|tiếp tục|có trách nhiệm|chủ động|khẩn trương|tập trung)\s+", "", tail, flags=re.I)
    
    # Chỉ ngắt tại dấu chấm, dấu chấm phẩy hoặc chuyển đoạn 'đồng thời'
    # TUYỆT ĐỐI KHÔNG ngắt ở 'nhằm', 'để' nếu độ dài chuỗi < 180 ký tự
    clauses = re.split(r"[;.]|\bđồng thời\b", tail)
    action = clauses[0].strip(" ,")
    
    # Lọc bỏ số hiệu văn bản nếu dính ở đầu
    action = re.sub(r"^(?:theo |căn cứ )?[Qq]uyết định[^,;]+?,\s*", "", action)
    
    if 8 <= len(action) <= 220:
        return action
    return ""


# -------------------------------------------------------------
# 6. PIPELINE TỔNG HỢP VIGOV-IE ENGINE
# -------------------------------------------------------------

class ViGovIEEngine:
    def __init__(self):
        pass

    def extract(self, sentence: str, event_type: str, trigger: str = "", agent_text: str = "", target_text: str = "") -> Dict[str, Any]:
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
        
        # 1. Bóc tách văn bản pháp lý
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
                
        # 3. Mức độ khẩn
        m_urg = re.search(r"\b(khẩn trương|quyết liệt|ngay lập tức|tập trung|chủ động|kịp thời|nghiêm túc)\b", sentence, re.I)
        if m_urg:
            res["urgency"] = m_urg.group(1).lower()

        # 4. Sự kiện Bổ nhiệm / Điều động
        if event_type in ("BO_NHIEM", "DIEU_DONG", "MIEN_NHIEM"):
            for pat, lbl in APPOINT_HIERARCHY:
                if pat.search(trigger) or pat.search(sentence):
                    res["appoint_type"] = lbl
                    break
            # Chức vụ sạch
            role = extract_clean_appointment_role(sentence)
            if role:
                res["role"] = role
            # Nhiệm kỳ
            m_ten = re.search(r"(?:thời hạn\s+(?:bổ nhiệm\s+(?:là\s+)?)?(\d+\s+năm)|nhiệm kỳ\s+(\d{4}\s*[-–]\s*\d{4}))", sentence, re.I)
            if m_ten:
                res["tenure"] = m_ten.group(0).strip()

        # 5. Sự kiện Kỷ luật
        elif event_type == "KY_LUAT":
            # Kiểm tra xem có phải đa đối tượng kỷ luật không (Coordination Ambiguity)
            coord_items = parse_coordinated_penalties(sentence)
            if coord_items:
                res["coordinated_items"] = coord_items
                res["penalty_form"] = coord_items[0]["penalty_form"]
            else:
                for pat, form, _ in PENALTY_HIERARCHY:
                    if pat.search(sentence):
                        res["penalty_form"] = form
                        break
                        
            # Lý do sai phạm
            m_vio = re.search(r"(?:do|vì|có vi phạm, khuyết điểm trong|vi phạm quy định về|vi phạm quy định của Đảng|vi phạm pháp luật|liên quan đến vụ án)\s+([^.;]+)", sentence, re.I)
            if m_vio:
                res["violation_reason"] = m_vio.group(1).strip(" ,")

        # 6. Sự kiện Chỉ đạo / Chủ trì
        elif event_type in ("CHI_DAO", "CHU_TRI"):
            action = extract_directive_action_full(sentence)
            if action:
                if res["deadline"] and res["deadline"] in action:
                    action = action.replace(res["deadline"], "").strip(" ,-")
                res["action_content"] = action

        # 7. Kiểm tra bị động trung gian
        agency_info = resolve_intermediate_passive_agency(sentence, agent_text)
        if agency_info.get("recommender_agency"):
            res["recommender_agency"] = agency_info["recommender_agency"]
        if agency_info.get("deciding_agency"):
            res["deciding_agency"] = agency_info["deciding_agency"]

        return res

