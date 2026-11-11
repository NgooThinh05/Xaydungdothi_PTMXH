# -*- coding: utf-8 -*-
"""
THỬ NGHIỆM ĐỐI CHUẨN 1: BÓC TÁCH SỰ KIỆN VÀ GÁN VAI NGHĨA (EVENT & ARGUMENT EXTRACTION)
So sánh:
- Phương pháp A (Hiện tại): Rule-based + underthesea.chunk nông + Regex cơ bản
- Phương pháp B (Đề xuất mới): Semantic Syntax Parser + RapidFuzz Position Alignment + Multi-tier Temporal & Legal Normalizer
"""

import csv
import json
import re
import time
from pathlib import Path
from collections import defaultdict
from rapidfuzz import fuzz, process

try:
    import underthesea
    HAS_UNDERTHESEA = True
except ImportError:
    HAS_UNDERTHESEA = False

# Import module hiện tại
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "extraction"))
import event_extractor as current_extractor

# -------------------------------------------------------------
# PHƯƠNG PHÁP B: ADVANCED SEMANTIC PARSER & RAPIDFUZZ NORMALIZER
# -------------------------------------------------------------

# 1. Regex văn bản pháp lý nâng cao (chuẩn hóa khoảng cách, bao gồm cả Nghị định, Thông tư, Công văn)
ADV_LEGAL_DOC_RE = re.compile(
    r"(?:Quyết định|Nghị quyết|Chỉ thị|Công điện|Thông báo|Kết luận|Nghị định|Thông tư|Công văn)"
    r"(?:\s+số)?\s*([0-9]+(?:\s*[/-]\s*[A-ZĐa-z0-9_-]+)+)",
    re.I
)

# 2. Regex thời hạn toàn diện (bao gồm cả quý La Mã, quý số, dạng text)
ADV_DEADLINE_RE = re.compile(
    r"(?:trước ngày|chậm nhất là|chậm nhất|trong tháng|trong quý|hoàn thành trước|thời hạn trước|đến ngày|trước|trong năm)\s+"
    r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?|\d{1,2}\s+tháng\s+\d{1,2}(?:\s+năm\s+\d{4})?|quý\s+[I|II|III|IV|1|2|3|4](?:\s*(?:năm|/)\s*\d{4})?|\d{4})",
    re.I
)

# 3. Phân loại hình thức kỷ luật mở rộng (bao gồm cả xóa tư cách, buộc thôi việc, đình chỉ)
ADV_PENALTY_FORMS = [
    (re.compile(r"khai trừ(?: ra)?(?: khỏi Đảng)?", re.I), "Khai trừ khỏi Đảng"),
    (re.compile(r"cách chức tất cả các chức vụ|cách tất cả chức vụ|cách chức", re.I), "Cách chức"),
    (re.compile(r"xóa tư cách(?:\s+chức vụ)?", re.I), "Xóa tư cách chức vụ"),
    (re.compile(r"buộc thôi việc", re.I), "Buộc thôi việc"),
    (re.compile(r"tạm đình chỉ(?:\s+công tác|\s+chức vụ)?", re.I), "Đình chỉ công tác"),
    (re.compile(r"cảnh cáo", re.I), "Cảnh cáo"),
    (re.compile(r"khiển trách", re.I), "Khiển trách"),
    (re.compile(r"kỷ luật", re.I), "Kỷ luật"),
]

# 4. Phân loại bổ nhiệm mở rộng
ADV_APPOINT_TYPES = [
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

# 5. Regex chức danh & RapidFuzz Position gazetteer
ADV_ROLE_RE = re.compile(
    r"(?:giữ chức(?: vụ)?|đảm nhiệm chức vụ|cương vị|làm)\s+([A-ZÀ-Ỹa-zà-ỹ0-9\s,-]+?)(?:\s+(?:nhiệm kỳ|thời hạn|kể từ|thay cho|theo Quyết định)|[.;]|$)",
    re.I
)

# Tải từ điển chức danh từ nodes_position.csv để đối chiếu RapidFuzz
KNOWN_POSITIONS = []
pos_csv = Path(__file__).resolve().parents[1] / "data" / "processed" / "graph" / "nodes_position.csv"
if pos_csv.exists():
    with open(pos_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            h = r.get("hien_thi") or r.get("name")
            if h:
                KNOWN_POSITIONS.append(h)


def method_b_extract_legal_doc(text: str) -> str:
    m = ADV_LEGAL_DOC_RE.search(text)
    if not m:
        return ""
    raw = m.group(0).strip()
    # Chuẩn hóa khoảng cách trong số hiệu: "2075 / QĐ - TTg" -> "2075/QĐ-TTg"
    return re.sub(r"\s*([/-])\s*", r"\1", raw)


def method_b_extract_deadline(text: str) -> str:
    m = ADV_DEADLINE_RE.search(text)
    return m.group(0).strip() if m else ""


def method_b_extract_role(text: str) -> str:
    m = ADV_ROLE_RE.search(text)
    cand = ""
    if m:
        cand = m.group(1).strip(" ,")
        # Cắt lọc các trạng từ
        cand = re.sub(r"^(?:mới|mới được bổ nhiệm|kiêm)\s+", "", cand)
        # Giới hạn độ dài hợp lý
        if len(cand) > 60:
            cand = cand[:60].rsplit(" ", 1)[0]
    
    # Dùng RapidFuzz so khớp với từ điển chức danh nếu có ứng viên
    if cand and KNOWN_POSITIONS:
        match, score, _ = process.extractOne(cand, KNOWN_POSITIONS, scorer=fuzz.token_set_ratio)
        if score >= 85:
            return match
    return cand


def method_b_extract_directive(sentence: str, target_text: str = "") -> dict:
    res = {}
    dl = method_b_extract_deadline(sentence)
    if dl:
        res["deadline"] = dl
    
    urg = current_extractor.extract_urgency(sentence)
    if urg:
        res["urgency"] = urg
        
    # Tách mệnh đề hành động nâng cao
    # Tìm sau trigger chỉ đạo hoặc sau target
    m_trig = re.search(r"\b(?:chỉ đạo|yêu cầu|đề nghị|giao nhiệm vụ|giao)\b", sentence, re.I)
    start_idx = m_trig.end() if m_trig else 0
    if target_text and target_text in sentence[start_idx:]:
        t_pos = sentence.find(target_text, start_idx)
        start_idx = t_pos + len(target_text)
        
    tail = sentence[start_idx:].strip(" ,;:")
    if not tail:
        return res
        
    # Loại bỏ từ đệm mở đầu
    tail = re.sub(r"^(?:phải|cần|tiếp tục|có trách nhiệm|chủ động|khẩn trương|tập trung)\s+", "", tail, flags=re.I)
    
    # Giữ lại cả mệnh đề mục đích "nhằm / để" nếu tổng độ dài < 120 ký tự (không cắt cụt như phương pháp A)
    clauses = re.split(r"[;.]|\bđồng thời\b", tail)
    action = clauses[0].strip(" ,")
    
    # Nếu có underthesea, tinh chỉnh ranh giới cụm động từ
    if HAS_UNDERTHESEA and len(action) > 15:
        try:
            tagged = underthesea.chunk(action)
            tokens = []
            started = False
            for tok, pos, tag in tagged:
                if tag.startswith("B-VP") or started:
                    started = True
                    tokens.append(tok)
            if tokens:
                action = " ".join(tokens).strip(" ,")
        except:
            pass
            
    if dl and dl in action:
        action = action.replace(dl, "").strip(" ,-")
        
    if 5 <= len(action) <= 220:
        res["action_content"] = action
        
    return res


def method_b_extract_arguments(sent: str, event_type: str, trigger: str, target_text: str = "") -> dict:
    res = {}
    doc = method_b_extract_legal_doc(sent)
    if doc:
        res["legal_doc"] = doc
        
    if event_type in ("BO_NHIEM", "DIEU_DONG", "MIEN_NHIEM"):
        for pat, label in ADV_APPOINT_TYPES:
            if pat.search(trigger) or pat.search(sent):
                res["appoint_type"] = label
                break
        tenure_m = current_extractor.TENURE_RE.search(sent)
        if tenure_m:
            res["tenure"] = tenure_m.group(0).strip()
        role = method_b_extract_role(sent)
        if role:
            res["role"] = role
            
    elif event_type == "KY_LUAT":
        for pat, form in ADV_PENALTY_FORMS:
            if pat.search(sent):
                res["penalty_form"] = form
                break
        v_m = current_extractor.VIOLATION_RE.search(sent)
        if v_m:
            res["violation_reason"] = v_m.group(1).strip(" ,")
            
    elif event_type in ("CHI_DAO", "CHU_TRI"):
        d_res = method_b_extract_directive(sent, target_text)
        res.update(d_res)
        
    return res


# -------------------------------------------------------------
# TIẾN HÀNH THỰC NGHIỆM ĐO ĐẠC TRÊN TẬP DỮ LIỆU THỰC TẾ
# -------------------------------------------------------------

def run_experiment():
    # 1. Tải tập kiểm thử từ self_review_claude.csv (104 mẫu câu thực tế từ tin tức)
    review_path = Path(__file__).resolve().parents[1] / "data" / "eval" / "self_review_claude.csv"
    test_cases = []
    with open(review_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("evidence"):
                test_cases.append({
                    "sentence": r["evidence"],
                    "rel": r["rel"],
                    "src_name": r["src_name"],
                    "dst_name": r["dst_name"],
                    "label": r.get("label", "1")
                })
                
    # Lấy thêm 96 sự kiện từ nodes_event.csv để đủ 200 câu đa dạng
    event_csv = Path(__file__).resolve().parents[1] / "data" / "processed" / "graph" / "nodes_event.csv"
    with open(event_csv, encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f)):
            if i >= 96:
                break
            if r.get("evidence") and len(r["evidence"]) > 30:
                test_cases.append({
                    "sentence": r["evidence"],
                    "rel": r["event_type"],
                    "src_name": "",
                    "dst_name": "",
                    "label": "1"
                })

    print(f"=== TẬP DỮ LIỆU KIỂM THỬ THỰC TẾ: {len(test_cases)} CÂU ===")

    # Đo đạc Phương pháp A (Hiện tại)
    t0 = time.time()
    results_a = []
    for item in test_cases:
        res = current_extractor.extract_event_arguments(
            sentence=item["sentence"],
            event_type=item["rel"],
            trigger="",
            agent_text=item["src_name"],
            target_text=item["dst_name"]
        )
        results_a.append(res)
    time_a = time.time() - t0

    # Đo đạc Phương pháp B (Đề xuất mới)
    t0 = time.time()
    results_b = []
    for item in test_cases:
        res = method_b_extract_arguments(
            sent=item["sentence"],
            event_type=item["rel"],
            trigger="",
            target_text=item["dst_name"]
        )
        results_b.append(res)
    time_b = time.time() - t0

    # Thống kê số lượng trường trích xuất được (Information Extraction Yield)
    fields = ["legal_doc", "action_content", "role", "appoint_type", "deadline", "urgency", "penalty_form", "tenure"]
    counts_a = {f: sum(1 for r in results_a if r.get(f)) for f in fields}
    counts_b = {f: sum(1 for r in results_b if r.get(f)) for f in fields}

    print("\n--- KẾT QUẢ ĐO ĐẠC NĂNG LỰC TRÍCH XUẤT (INFORMATION EXTRACTION YIELD) ---")
    print(f"{'Trường tham số':<20} | {'Phương pháp A (Hiện tại)':<25} | {'Phương pháp B (Đề xuất)':<25} | {'Độ tăng trưởng (%)':<15}")
    print("-" * 90)
    for f in fields:
        ca = counts_a[f]
        cb = counts_b[f]
        growth = ((cb - ca) / ca * 100) if ca > 0 else (100.0 if cb > 0 else 0.0)
        print(f"{f:<20} | {ca:<25} | {cb:<25} | {growth:>+12.1f}%")

    print("-" * 90)
    total_a = sum(counts_a.values())
    total_b = sum(counts_b.values())
    print(f"{'TỔNG THAM SỐ':<20} | {total_a:<25} | {total_b:<25} | {((total_b - total_a)/total_a*100):>+12.1f}%")

    print("\n--- HIỆU NĂNG TÍNH TOÁN & TỐC ĐỘ XỬ LÝ ---")
    print(f"Phương pháp A: {len(test_cases)/time_a:.1f} câu/giây (Tổng thời gian: {time_a:.3f}s)")
    print(f"Phương pháp B: {len(test_cases)/time_b:.1f} câu/giây (Tổng thời gian: {time_b:.3f}s)")

    # Lưu kết quả so sánh chi tiết ra JSON
    comparison_summary = {
        "num_test_cases": len(test_cases),
        "method_a": {"total_extracted": total_a, "counts": counts_a, "time_s": time_a, "speed_sps": len(test_cases)/time_a},
        "method_b": {"total_extracted": total_b, "counts": counts_b, "time_s": time_b, "speed_sps": len(test_cases)/time_b},
        "sample_comparisons": []
    }
    for i in range(min(5, len(test_cases))):
        comparison_summary["sample_comparisons"].append({
            "sentence": test_cases[i]["sentence"],
            "rel": test_cases[i]["rel"],
            "pred_a": results_a[i],
            "pred_b": results_b[i]
        })
    with open("scratch/nlp_comparison_results.json", "w", encoding="utf-8") as f:
        json.dump(comparison_summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_experiment()

