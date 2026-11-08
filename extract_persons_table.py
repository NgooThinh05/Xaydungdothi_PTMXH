import json
import re
import sys
import sqlite3
import os
from collections import defaultdict

# Fix encoding cho Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Thử nạp thư viện NLP tiếng Việt underthesea (nếu có cài đặt)
try:
    from underthesea import ner
    HAS_UNDERTHESEA = True
except ImportError:
    HAS_UNDERTHESEA = False
    print("[!] Chưa cài 'underthesea'. Hệ thống sẽ dùng bộ quy tắc Báo chí Tiếng Việt (Rule-based).")

# ================= CẤU HÌNH FILE =================
INPUT_ARTICLES_JSON = "baomoi_political_corpus.jsonl"  # File 5000 bài báo từ bước trước
OUTPUT_PERSONS_JSON = "baomoi_persons_political_table.json"           # Bảng nhân vật dạng JSON
OUTPUT_PERSONS_CSV = "baomoi_persons_political_table.csv"             # Bảng nhân vật mở bằng Excel
OUTPUT_SQLITE_DB = "baomoi_knowledge_graph1.db"              # Cơ sở dữ liệu SQLite (2 bảng liên kết)
# =================================================

# ============ DANH XƯNG ============
HONORIFICS = [
    "ông", "bà", "bác",
]

# ============ CHỨC VỤ CHÍNH TRỊ GIA VIỆT NAM ============
# Chỉ giữ lại các chức danh trong hệ thống chính trị, nhà nước, đảng, quân đội
TITLES_PREFIX = [
    # Lãnh đạo cấp cao
    "tổng bí thư", "chủ tịch nước", "thủ tướng", "phó thủ tướng",
    "chủ tịch quốc hội", "phó chủ tịch quốc hội",
    "thường trực ban bí thư",
    # Chính phủ
    "bộ trưởng", "thứ trưởng", "phó thủ tướng chính phủ",
    # Đảng - cấp trung ương
    "ủy viên bộ chính trị", "ủy viên trung ương đảng",
    "bí thư trung ương đảng", "trưởng ban tổ chức trung ương",
    "trưởng ban tuyên giáo trung ương", "trưởng ban nội chính trung ương",
    "trưởng ban dân vận trung ương", "trưởng ban kinh tế trung ương",
    "trưởng ban đối ngoại trung ương",
    "chủ nhiệm ủy ban kiểm tra trung ương",
    "phó trưởng ban tổ chức trung ương", "phó trưởng ban tuyên giáo trung ương",
    "phó trưởng ban nội chính trung ương",
    # Quốc hội
    "chủ nhiệm ủy ban", "phó chủ nhiệm ủy ban",
    "chủ nhiệm văn phòng quốc hội",
    "tổng thư ký quốc hội",
    "trưởng đoàn đại biểu quốc hội", "đại biểu quốc hội",
    # Đảng - cấp tỉnh/thành
    "bí thư", "phó bí thư", "bí thư tỉnh ủy", "phó bí thư tỉnh ủy",
    "bí thư thành ủy", "phó bí thư thành ủy",
    "bí thư huyện ủy", "phó bí thư huyện ủy",
    "bí thư quận ủy", "phó bí thư quận ủy",
    "bí thư đảng ủy",
    # UBND / HĐND
    "chủ tịch ubnd", "phó chủ tịch ubnd",
    "chủ tịch hđnd", "phó chủ tịch hđnd",
    "chủ tịch ủy ban nhân dân", "phó chủ tịch ủy ban nhân dân",
    "chủ tịch hội đồng nhân dân", "phó chủ tịch hội đồng nhân dân",
    "chủ tịch", "phó chủ tịch",
    # Cơ quan tư pháp, thanh tra, kiểm toán
    "chánh án", "phó chánh án",
    "viện trưởng viện kiểm sát", "phó viện trưởng viện kiểm sát",
    "viện trưởng", "phó viện trưởng",
    "tổng thanh tra chính phủ", "phó tổng thanh tra",
    "chánh thanh tra", "phó chánh thanh tra",
    "tổng kiểm toán nhà nước", "phó tổng kiểm toán",
    # Cấp sở, ban ngành
    "giám đốc sở", "phó giám đốc sở",
    "giám đốc công an", "phó giám đốc công an",
    "trưởng ban", "phó trưởng ban",
    "chánh văn phòng", "phó chánh văn phòng",
    "vụ trưởng", "phó vụ trưởng",
    "cục trưởng", "phó cục trưởng",
    "tổng cục trưởng", "phó tổng cục trưởng",
    # Quân đội - Công an (cấp tướng, tá – thường gắn với chính trị)
    "thượng tướng", "trung tướng", "thiếu tướng",
    "đại tá", "thượng tá",
    # Mặt trận tổ quốc
    "chủ tịch mặt trận tổ quốc", "phó chủ tịch mặt trận tổ quốc",
    "chủ tịch ủy ban mặt trận", "phó chủ tịch ủy ban mặt trận",
    # Chính trị gia quốc tế (để bắt khi xuất hiện trong bài về VN)
    "tổng thống", "cựu tổng thống", "phó tổng thống",
    "ngoại trưởng", "bộ trưởng ngoại giao",
    "thượng nghị sĩ", "hạ nghị sĩ", "nghị sĩ",
    "nguyên thủ", "thủ tướng",
    "tổng thư ký liên hợp quốc",
    # Chức danh khác có tính chính trị
    "nguyên bộ trưởng", "nguyên thứ trưởng", "nguyên chủ tịch",
    "nguyên phó chủ tịch", "nguyên bí thư", "nguyên phó bí thư",
    "nguyên thủ tướng", "nguyên phó thủ tướng",
    "nguyên tổng bí thư", "nguyên chủ tịch nước",
    "nguyên chủ tịch quốc hội",
]

# ============ TỪ KHÓA CHÍNH TRỊ - dùng để lọc nhân vật ============
# Nếu chức vụ hoặc tổ chức chứa bất kỳ từ khóa nào dưới đây → là chính trị gia
POLITICAL_KEYWORDS = [
    # Chức vụ chính trị
    "tổng bí thư", "chủ tịch nước", "thủ tướng", "phó thủ tướng",
    "chủ tịch quốc hội", "phó chủ tịch quốc hội",
    "bộ trưởng", "thứ trưởng",
    "bí thư", "phó bí thư",
    "chủ tịch ubnd", "phó chủ tịch ubnd",
    "chủ tịch hđnd", "phó chủ tịch hđnd",
    "chủ tịch ủy ban", "phó chủ tịch ủy ban",
    "chủ tịch hội đồng", "phó chủ tịch hội đồng",
    "chủ tịch mặt trận", "phó chủ tịch mặt trận",
    "ủy viên bộ chính trị", "ủy viên trung ương",
    "đại biểu quốc hội",
    "chánh án", "phó chánh án",
    "viện trưởng viện kiểm sát", "phó viện trưởng viện kiểm sát",
    "tổng thanh tra", "phó tổng thanh tra",
    "chánh thanh tra", "phó chánh thanh tra",
    "tổng kiểm toán", "phó tổng kiểm toán",
    "giám đốc sở", "phó giám đốc sở",
    "giám đốc công an", "phó giám đốc công an",
    "trưởng ban", "phó trưởng ban",
    "chánh văn phòng", "phó chánh văn phòng",
    "vụ trưởng", "phó vụ trưởng",
    "cục trưởng", "phó cục trưởng",
    "tổng cục trưởng", "phó tổng cục trưởng",
    "chủ nhiệm", "phó chủ nhiệm",
    "tổng thư ký quốc hội",
    # Quân đội / Công an cấp cao
    "thượng tướng", "trung tướng", "thiếu tướng",
    # Chính trị quốc tế
    "tổng thống", "phó tổng thống", "ngoại trưởng",
    "thượng nghị sĩ", "hạ nghị sĩ", "nghị sĩ",
    "nguyên thủ",
    # Từ khóa chung mang tính chính trị
    "nguyên bộ trưởng", "nguyên thứ trưởng",
    "nguyên chủ tịch", "nguyên phó chủ tịch",
    "nguyên bí thư", "nguyên phó bí thư",
    "nguyên thủ tướng", "nguyên phó thủ tướng",
    "nguyên tổng bí thư", "nguyên chủ tịch nước",
    "nguyên chủ tịch quốc hội",
]

# Tên tổ chức chính trị / nhà nước – nhân vật thuộc các tổ chức này = chính trị gia
POLITICAL_ORG_KEYWORDS = [
    "quốc hội", "chính phủ", "nhà nước", "đảng",
    "tỉnh ủy", "thành ủy", "huyện ủy", "quận ủy", "đảng ủy", "đảng bộ",
    "ubnd", "ủy ban nhân dân", "hđnd", "hội đồng nhân dân",
    "mặt trận tổ quốc", "ủy ban mặt trận",
    "ban tổ chức trung ương", "ban tuyên giáo", "ban nội chính",
    "ban dân vận", "ban kinh tế trung ương", "ban đối ngoại",
    "ủy ban kiểm tra", "thanh tra chính phủ", "kiểm toán nhà nước",
    "bộ công an", "bộ quốc phòng", "bộ ngoại giao", "bộ nội vụ",
    "bộ tư pháp", "bộ tài chính", "bộ kế hoạch", "bộ công thương",
    "bộ xây dựng", "bộ giao thông", "bộ y tế", "bộ giáo dục",
    "bộ nông nghiệp", "bộ tài nguyên", "bộ lao động",
    "bộ văn hóa", "bộ khoa học", "bộ thông tin",
    "tòa án nhân dân", "viện kiểm sát nhân dân",
    "công an tỉnh", "công an thành phố", "công an huyện",
    "sở nội vụ", "sở tư pháp", "sở tài chính", "sở kế hoạch",
    "sở công thương", "sở xây dựng", "sở giao thông", "sở y tế",
    "sở giáo dục", "sở nông nghiệp", "sở tài nguyên", "sở lao động",
    "sở văn hóa", "sở khoa học", "sở thông tin",
]

# ============ TỪ LOẠI TRỪ - KHÔNG PHẢI TÊN NGƯỜI ============

# Tên địa danh, tổ chức, thực thể không phải người
NON_PERSON_PATTERNS = [
    # Tổ chức hành chính
    r"^(?:UBND|HĐND|Sở |Bộ |Ban |Viện |Trường |Bệnh viện|Tập đoàn|Công ty|Ngân hàng|"
    r"CLB |Đội tuyển|Ủy ban|Tòa án|Công an |Quân đội|Trung tâm|Hội đồng|Cục |Chi cục|"
    r"Phòng |Đảng ủy|Tỉnh ủy|Thành ủy|Huyện ủy|Quận ủy|Đảng bộ|Liên đoàn|"
    r"Chính phủ|Quốc hội|Nhà nước|Mặt trận|Đoàn |Hội )",
    # Địa danh Việt Nam
    r"^(?:Việt Nam|Hà Nội|Đà Nẵng|Hải Phòng|Cần Thơ|Nghệ An|Thanh Hóa|Quảng Ninh|"
    r"Bắc Giang|Bắc Ninh|Hải Dương|Vĩnh Phúc|Thái Nguyên|Lạng Sơn|Quảng Nam|"
    r"Bình Dương|Đồng Nai|Long An|Tiền Giang|Bình Thuận|Khánh Hòa|Phú Yên|"
    r"Gia Lai|Đắk Lắk|Lâm Đồng|Kon Tum|Sóc Trăng|Cà Mau|Bạc Liêu|Trà Vinh|"
    r"Hậu Giang|Vĩnh Long|An Giang|Kiên Giang|Đồng Tháp|Bến Tre|Tây Ninh|"
    r"Bình Phước|Bà Rịa|Ninh Thuận|Ninh Bình|Nam Định|Thái Bình|Hưng Yên|"
    r"Hà Nam|Phú Thọ|Yên Bái|Lào Cai|Hà Giang|Cao Bằng|Tuyên Quang|Bắc Kạn|"
    r"Sơn La|Điện Biên|Lai Châu|Hòa Bình|Quảng Bình|Quảng Trị|Thừa Thiên|"
    r"Phú Quốc|Côn Đảo|Hạ Long)$",
    # Địa danh quốc tế
    r"^(?:Trung Quốc|Hoa Kỳ|Nga|Nhật Bản|Hàn Quốc|Thái Lan|Châu Âu|Liên Hợp Quốc|"
    r"Israel|Palestine|Iran|Iraq|Syria|Ukraine|Philippines|Indonesia|Malaysia|Singapore|"
    r"Myanmar|Campuchia|Lào|Ấn Độ|Pakistan|Afghanistan|Triều Tiên|Đài Loan|"
    r"Đức|Pháp|Anh|Ý|Tây Ban Nha|Bồ Đào Nha|Thụy Sĩ|Hà Lan|Bỉ|Áo|"
    r"Canada|Mexico|Brazil|Argentina|Úc|New Zealand|"
    r"Washington|Moscow|Bắc Kinh|Tokyo|Seoul|London|Paris|Berlin)$",
    # Tên đảng phái, tôn giáo
    r"^(?:Đảng Cộng sản|Đảng Dân chủ|Đảng Cộng hòa|Hamas|Hezbollah|Taliban|NATO|ASEAN|EU|WHO|FIFA|AFC)$",
    # Tên tổ chức 2 từ phổ biến hay bị bắt nhầm thành tên người
    r"^(?:Công Thương|Công An|Tài Chính|Nội Vụ|Tư Pháp|Ngoại Giao|Quốc Phòng|Xây Dựng|"
    r"Giao Thông|Y Tế|Giáo Dục|Nông Nghiệp|Văn Hóa|Khoa Học|Tài Nguyên|Lao Động|"
    r"Công Nghệ|Thông Tin|Kế Hoạch|Đầu Tư|Vụ Giáo|Vụ Pháp|Vụ Tài|Vụ Kế|"
    r"Công Nghiệp|Dân Tộc|Thanh Tra|Kiểm Toán|Quốc Hội|Mặt Trận|Hội Đồng|"
    r"Ban Tuyên|Ban Dân|Ban Kinh|Ban Nội|Ban Tổ|Ban Chỉ)$",
]
NON_PERSON_COMPILED = [re.compile(p, re.IGNORECASE) for p in NON_PERSON_PATTERNS]

# Từ khóa chắc chắn KHÔNG phải tên người khi xuất hiện trong "tên"
NON_PERSON_KEYWORDS = {
    "cho biết", "chia sẻ", "nhấn mạnh", "cho rằng", "nói rằng", "nói thêm",
    "khẳng định", "trình bày", "đề xuất", "phát biểu", "thông tin",
    "công bố", "tuyên bố", "cảnh báo", "kêu gọi", "yêu cầu", "đề nghị",
    "nhận định", "đánh giá", "phân tích", "giải thích", "lý giải",
    "lưu ý", "khuyến cáo", "hướng dẫn", "chỉ đạo", "ban hành",
    "triển khai", "thực hiện", "tiến hành", "phối hợp", "tổ chức",
    "sinh năm", "học sinh", "mất việc", "có hoàn cảnh", "trúng tuyển",
    "liệt sĩ", "anh hùng", "an ninh", "an nghỉ", "ban đầu",
    "và Phu nhân", "cùng Nhà Vua", "và Tổng",
}


def is_politician(role_titles: set, organizations: set) -> bool:
    """
    Kiểm tra xem nhân vật có phải là chính trị gia hay không
    dựa trên chức vụ (role_titles) và tổ chức (organizations).
    
    Trả về True nếu BẤT KỲ chức vụ hoặc tổ chức nào chứa từ khóa chính trị.
    """
    # Kiểm tra chức vụ
    for role in role_titles:
        role_lower = role.lower().strip()
        if not role_lower:
            continue
        for kw in POLITICAL_KEYWORDS:
            if kw in role_lower:
                return True

    # Kiểm tra tổ chức
    for org in organizations:
        org_lower = org.lower().strip()
        if not org_lower:
            continue
        for kw in POLITICAL_ORG_KEYWORDS:
            if kw in org_lower:
                return True

    return False


def is_valid_vietnamese_name(name: str) -> bool:
    """
    Kiểm tra nghiêm ngặt xem một chuỗi có phải là tên người Việt hoặc tên người nước ngoài hợp lệ.
    
    Quy tắc tên người Việt:
    - Từ 2-4 âm tiết, MỖI từ đều viết hoa chữ cái đầu
    - Không chứa động từ, tính từ, liên từ viết thường
    - Không phải tên tổ chức, địa danh
    
    Quy tắc tên nước ngoài:
    - Cho phép giới từ viết thường (de, di, von, van, al, el, bin, ibn)
    - Từ 2-5 âm tiết
    """
    if not name or len(name) < 3:
        return False

    # Loại bỏ tên chứa viết tắt tổ chức (tất cả chữ hoa, >= 2 ký tự, VD: CATP, TP, UBND)
    words_check = name.split()
    for w in words_check:
        if len(w) >= 2 and w.isupper() and w.isalpha():
            return False

    # Kiểm tra NON_PERSON_KEYWORDS
    name_lower = name.lower()
    for kw in NON_PERSON_KEYWORDS:
        if kw in name_lower:
            return False

    # Kiểm tra NON_PERSON_PATTERNS
    for pat in NON_PERSON_COMPILED:
        if pat.search(name):
            return False

    words = name.split()
    if len(words) < 2 or len(words) > 5:
        return False

    # Các giới từ hợp lệ trong tên nước ngoài (viết thường)
    foreign_prepositions = {"de", "di", "do", "da", "von", "van", "der", "den",
                            "al", "el", "bin", "ibn", "ben", "le", "la", "du",
                            "mc", "mac", "o'"}

    # Các từ viết thường phổ biến trong tiếng Việt KHÔNG BAO GIỜ có trong tên người
    vn_common_words = {
        "và", "của", "các", "này", "đã", "đang", "sẽ", "được", "không", "có",
        "là", "trong", "ngoài", "trên", "dưới", "với", "cho", "tại", "từ", "đến",
        "về", "theo", "qua", "lại", "ra", "vào", "lên", "xuống", "bằng", "cùng",
        "hay", "hoặc", "nhưng", "mà", "nên", "vì", "do", "khi", "nếu", "tuy",
        "cũng", "đều", "rất", "quá", "hơn", "nhất", "nào", "gì", "sao",
        "mới", "vẫn", "còn", "đó", "đây", "kia", "ấy",
        "biết", "rằng", "thêm", "thì", "nhiều", "ít", "lớn", "nhỏ",
        "thuộc", "liên", "tổ", "chức", "hợp", "phát", "hiện",
        # Động từ phổ biến
        "nói", "cho", "lấy", "tạo", "điều", "chỉnh", "phá", "kêu",
        "mất", "tìm", "thấy", "xử", "lý", "ký", "ban", "hành",
        "trình", "bày", "triển", "khai", "tiến", "dẫn", "đặt",
        "gọi", "góp", "cứu", "làm", "đưa", "đến",
    }

    has_uppercase_word = False
    for i, w in enumerate(words):
        if w.lower() in foreign_prepositions:
            continue  # Cho phép giới từ nước ngoài viết thường

        if w[0].isupper():
            has_uppercase_word = True
            # Kiểm tra phần còn lại phải là chữ cái (cho phép dấu, gạch ngang)
            rest = w[1:]
            if rest and not re.match(r"^[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđA-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ'\-]+$", rest):
                return False
        elif w.lower() in vn_common_words:
            return False  # Chứa từ thông thường viết thường -> không phải tên
        elif w[0].islower():
            # Từ viết thường không nằm trong danh sách giới từ nước ngoài 
            # và không phải ngoại lệ -> không hợp lệ
            return False

    if not has_uppercase_word:
        return False

    # Từ đầu tiên PHẢI viết hoa (trừ giới từ nước ngoài)
    if words[0][0].islower() and words[0].lower() not in foreign_prepositions:
        return False

    return True


def split_sentences(text: str) -> list[str]:
    """Tách văn bản bài báo thành danh sách các câu."""
    raw_sents = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [s.strip() for s in raw_sents if len(s.strip()) > 10]


def extract_age_and_location(sentence: str, person_name: str) -> tuple[int | None, str]:
    """
    Bóc tách tuổi/năm sinh và nơi cư trú thường nằm trong ngoặc đơn ngay sau tên nhân vật.
    VD: "Nguyễn Văn A (35 tuổi, ngụ quận Bình Thạnh, TP.HCM)" hoặc "(SN 1988, quê Nghệ An)"
    """
    age = None
    location = ""

    # Tìm cụm ngoặc đơn nằm ngay sau tên nhân vật
    pattern = re.escape(person_name) + r"\s*\(([^)]+)\)"
    match = re.search(pattern, sentence)
    if match:
        inside_paren = match.group(1)
        # Bắt tuổi: "35 tuổi" hoặc "SN 1989" / "sinh năm 1989"
        age_match = re.search(r"(\d{1,2})\s*tuổi", inside_paren, re.IGNORECASE)
        birth_match = re.search(r"(?:sn|sinh năm)\s*(\d{4})", inside_paren, re.IGNORECASE)

        if age_match:
            age = int(age_match.group(1))
        elif birth_match:
            birth_year = int(birth_match.group(1))
            age = 2026 - birth_year  # Quy đổi ra tuổi hiện tại

        # Bắt địa chỉ/quê quán: "trú tại...", "ngụ...", "quê...", "ở..."
        loc_match = re.search(
            r"(?:trú tại|trú|ngụ tại|ngụ|quê|ở tại|ở)\s+([^,;]+(?:,\s*[^,;]+)?)",
            inside_paren, re.IGNORECASE
        )
        if loc_match:
            location = loc_match.group(1).strip()

    return age, location


def extract_organization(sentence: str, person_name: str) -> str:
    """Bắt tên Tổ chức / Cơ quan đi kèm chức vụ của nhân vật trong câu."""
    org_patterns = [
        r"(?:Bộ|Sở|Viện|Trường|Bệnh viện|Tập đoàn|Công ty|Ngân hàng|CLB|Đội tuyển|"
        r"Ủy ban|UBND|Tòa án|Công an|Ban|Cục|Trung tâm|Liên đoàn|Hiệp hội)"
        r"\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
        r"[^\.,;(\n]{2,40}"
    ]
    for pat in org_patterns:
        m = re.search(pat, sentence)
        if m:
            return m.group(0).strip()
    return ""


def extract_quotes_from_sentence(sentence: str) -> list[str]:
    """Trích xuất câu nói trực tiếp trong dấu ngoặc kép "..." hoặc \u201c...\u201d."""
    quotes = re.findall(r'["\u201c]([^"\u201d]{15,300})["\u201d]', sentence)
    return [q.strip() for q in quotes]


def extract_name_after_prefix(text: str, match_end: int, vn_cap_word_pattern: str) -> str | None:
    """
    Trích xuất tên người ngay sau prefix (chức vụ/danh xưng).
    Dừng lại ngay khi gặp:
    - Dấu phẩy, dấu chấm, dấu ngoặc, dấu gạch ngang
    - Từ viết thường (trừ giới từ nước ngoài)
    - Hết câu
    """
    remaining = text[match_end:]

    # Bỏ khoảng trắng đầu
    remaining = remaining.lstrip()

    # Tìm chuỗi tên: các từ viết hoa liên tiếp (cho phép giới từ nước ngoài viết thường)
    foreign_preps = {"de", "di", "do", "da", "von", "van", "der", "den",
                     "al", "el", "bin", "ibn", "ben", "le", "la", "du"}

    name_words = []
    pos = 0
    while pos < len(remaining) and len(name_words) < 6:
        # Bỏ khoảng trắng
        while pos < len(remaining) and remaining[pos] == ' ':
            pos += 1
        if pos >= len(remaining):
            break

        # Dừng nếu gặp dấu câu hoặc dấu đặc biệt
        if remaining[pos] in ',.;:!?()[]{}\"\u201c\u201d\u2018\u2019-\u2013\u2014':
            break

        # Đọc từ tiếp theo
        word_start = pos
        while pos < len(remaining) and remaining[pos] not in ' ,.;:!?()[]{}\"\u201c\u201d\u2018\u2019-\u2013\u2014':
            pos += 1
        word = remaining[word_start:pos]

        if not word:
            break

        # Từ viết hoa
        if word[0].isupper():
            name_words.append(word)
        # Giới từ nước ngoài
        elif word.lower() in foreign_preps and name_words:
            name_words.append(word)
        else:
            # Gặp từ viết thường -> dừng
            break

    if len(name_words) >= 2:
        return " ".join(name_words)
    return None


def extract_persons_from_article(article: dict) -> list[dict]:
    """
    Hàm lõi: Quét toàn bộ 1 bài báo, nhận diện các nhân vật CHÍNH TRỊ GIA và gom nhóm thông tin.
    
    Quy trình:
    1. Regex bắt tên chính xác - dừng ngay khi gặp từ viết thường/dấu câu
    2. Xử lý cấu trúc dấu gạch ngang "Tên - Chức vụ" phổ biến trong báo VN
    3. Validate tên nghiêm ngặt qua is_valid_vietnamese_name()
    4. Gom nhóm biến thể tên
    5. Loại bỏ tổ chức, địa danh bị bắt nhầm
    6. **LỌC**: Chỉ giữ lại nhân vật có chức vụ/tổ chức CHÍNH TRỊ (is_politician)
    """
    full_text = f"{article.get('title', '')}. {article.get('sapo', '')}\n{article.get('content', '')}"
    sentences = split_sentences(full_text)

    # Từ điển gom thông tin theo từng nhân vật trong bài
    persons_map = {}

    # Regex nhận diện chức vụ/danh xưng
    titles_group = "|".join(sorted(TITLES_PREFIX + HONORIFICS, key=len, reverse=True))

    # Mẫu Việt Nam: 1 từ viết hoa (chữ cái đầu hoa, phần còn lại thường)
    vn_cap_word = (
        r"[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ"
        r"ÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
        r"[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
        r"ùúụủũưừứựửữỳýỵỷỹđ]+"
    )

    # ====== MẪU 1: Chức vụ/Danh xưng + Tên Viết Hoa ======
    # VD: "Thủ tướng Phạm Minh Chính", "Chủ tịch Tô Lâm"
    pattern_prefix = re.compile(
        rf"\b({titles_group})\s+",
        re.IGNORECASE
    )

    # ====== MẪU 2: [Danh xưng] Tên Viết Hoa - Chức vụ (dấu gạch ngang) ======
    # VD: "Nguyễn Văn A - Chủ tịch UBND tỉnh"
    pattern_dash_title = re.compile(
        rf"(?:({titles_group})\s+)?"
        rf"({vn_cap_word}(?:\s+{vn_cap_word}){{1,4}})"
        rf"\s*[-–—]\s*"
        rf"({titles_group})"
        rf"([^\.,;!?\n]{{0,60}})",
        re.IGNORECASE
    )

    # ====== MẪU 3: "Theo/Ông/Bà + Tên, chức vụ..." (dấu phẩy) ======
    # VD: "Theo ông Nguyễn Văn A, Giám đốc Sở Y tế,"
    pattern_comma_title = re.compile(
        rf"\b(?:theo\s+)?({titles_group})\s+"
        rf"({vn_cap_word}(?:\s+{vn_cap_word}){{1,4}})"
        rf"\s*,\s*"
        rf"({titles_group}[^\.,;!?\n]{{0,60}})",
        re.IGNORECASE
    )

    def add_person(name: str, honorific: str = "", role: str = "",
                   extra_role: str = "", sentence: str = ""):
        """Helper: Thêm hoặc cập nhật thông tin nhân vật vào persons_map."""
        name = name.strip()

        # Validate tên
        if not is_valid_vietnamese_name(name):
            return

        if name not in persons_map:
            persons_map[name] = {
                "person_name": name,
                "honorific": "",
                "role_title": set(),
                "organization": set(),
                "age": None,
                "location": "",
                "quotes": [],
                "actions_context": [],
                "mention_count": 0
            }

        p_info = persons_map[name]

        if honorific and not p_info["honorific"]:
            p_info["honorific"] = honorific.capitalize()

        if role:
            clean_role = role.strip().rstrip(",;.")
            if clean_role:
                p_info["role_title"].add(clean_role.capitalize())

        if extra_role:
            clean_extra = extra_role.strip().rstrip(",;.")
            if clean_extra:
                p_info["role_title"].add(clean_extra.capitalize())

    for sent in sentences:
        # ---------- MẪU 3 (ưu tiên cao nhất vì chính xác nhất): "Ông X, Giám đốc Y" ----------
        for match in pattern_comma_title.finditer(sent):
            prefix = match.group(1).strip()
            name = match.group(2).strip()
            role_after = match.group(3).strip()

            honorific = prefix.capitalize() if prefix.lower() in [h.lower() for h in HONORIFICS] else ""
            role_prefix = "" if prefix.lower() in [h.lower() for h in HONORIFICS] else prefix

            add_person(name, honorific=honorific, role=role_prefix, extra_role=role_after, sentence=sent)

        # ---------- MẪU 2: "[Danh xưng] Tên - Chức vụ" ----------
        for match in pattern_dash_title.finditer(sent):
            opt_prefix = match.group(1)  # Optional danh xưng/chức vụ trước tên
            name = match.group(2).strip()
            title = match.group(3).strip()
            title_rest = match.group(4).strip() if match.group(4) else ""
            # Cắt role_title: dừng tại dấu ngoặc đơn hoặc dấu gạch ngang thứ 2
            title_rest = re.split(r'[()\\-–—]', title_rest)[0].strip()
            full_role = f"{title} {title_rest}".strip().rstrip(",;.")

            honorific = ""
            role_from_prefix = ""
            if opt_prefix:
                if opt_prefix.lower() in [h.lower() for h in HONORIFICS]:
                    honorific = opt_prefix.capitalize()
                else:
                    role_from_prefix = opt_prefix
            else:
                # Fallback: tìm xem trước tên có danh xưng không
                before_name_pos = max(0, match.start() - 15)
                before_text = sent[before_name_pos:match.start()].lower().strip()
                for h in HONORIFICS:
                    if before_text.endswith(h):
                        honorific = h.capitalize()
                        break

            add_person(name, honorific=honorific, role=full_role, extra_role=role_from_prefix, sentence=sent)

        # ---------- MẪU 1: "Chức vụ/Danh xưng + Tên" ----------
        for match in pattern_prefix.finditer(sent):
            prefix = match.group(1).strip()

            # Trích xuất tên ngay sau prefix - dùng hàm riêng để dừng đúng chỗ
            name = extract_name_after_prefix(sent, match.end(), vn_cap_word)
            if not name:
                continue

            honorific = prefix.capitalize() if prefix.lower() in [h.lower() for h in HONORIFICS] else ""
            role = "" if prefix.lower() in [h.lower() for h in HONORIFICS] else prefix

            # Tìm thêm chức vụ sau tên (VD "Ông Nguyễn Văn A, Giám đốc Sở Y tế")
            # -> Đã xử lý bởi MẪU 3 ở trên, bỏ qua trùng lặp
            add_person(name, honorific=honorific, role=role, sentence=sent)

        # ---------- Bổ sung: underthesea NER ----------
        if HAS_UNDERTHESEA:
            try:
                ner_results = ner(sent)
                current_name_parts = []
                for word, pos, chunk, ner_tag in ner_results:
                    if "B-PER" in ner_tag:
                        if current_name_parts:
                            full_name = " ".join(current_name_parts)
                            add_person(full_name, sentence=sent)
                        current_name_parts = [word]
                    elif "I-PER" in ner_tag and current_name_parts:
                        current_name_parts.append(word)
                    else:
                        if current_name_parts:
                            full_name = " ".join(current_name_parts)
                            add_person(full_name, sentence=sent)
                            current_name_parts = []
                # Xử lý trường hợp tên nằm cuối câu
                if current_name_parts:
                    full_name = " ".join(current_name_parts)
                    add_person(full_name, sentence=sent)
            except Exception:
                pass

    # ====== BƯỚC 2: Gom nhóm biến thể tên (deduplication) ======
    canonical_names = {}  # mapping: biến thể -> tên chuẩn

    sorted_names = sorted(persons_map.keys(), key=len, reverse=True)  # Tên dài hơn ưu tiên
    for name in sorted_names:
        # Kiểm tra xem name có phải là phần đầu/cuối của tên dài hơn
        is_subname = False
        for canonical in canonical_names.values():
            if canonical != name and name in canonical:
                is_subname = True
                canonical_names[name] = canonical
                break
        if not is_subname:
            canonical_names[name] = name

    # Gộp thông tin từ biến thể vào tên chuẩn
    merged_map = {}
    for name, canonical in canonical_names.items():
        if canonical not in merged_map:
            merged_map[canonical] = persons_map.get(canonical, persons_map[name]).copy()
            merged_map[canonical]["role_title"] = set(merged_map[canonical]["role_title"])
            merged_map[canonical]["organization"] = set(merged_map[canonical]["organization"])
            merged_map[canonical]["quotes"] = list(merged_map[canonical]["quotes"])
            merged_map[canonical]["actions_context"] = list(merged_map[canonical]["actions_context"])

        if name != canonical and name in persons_map:
            src = persons_map[name]
            dst = merged_map[canonical]
            if src["honorific"] and not dst["honorific"]:
                dst["honorific"] = src["honorific"]
            dst["role_title"].update(src["role_title"])
            dst["organization"].update(src["organization"])
            if src["age"] and not dst["age"]:
                dst["age"] = src["age"]
            if src["location"] and not dst["location"]:
                dst["location"] = src["location"]

    persons_map = merged_map

    # ====== BƯỚC 3: Thu thập Tuổi, Địa chỉ, Tổ chức, Phát ngôn cho mỗi nhân vật ======
    for name, p_info in list(persons_map.items()):
        for sent in sentences:
            if name in sent:
                p_info["mention_count"] += sent.count(name)

                # Lưu ngữ cảnh hành động (tối đa 3 câu tiêu biểu nhất)
                if len(p_info["actions_context"]) < 3 and sent not in p_info["actions_context"]:
                    p_info["actions_context"].append(sent)

                # Trích xuất tuổi & nơi ở nếu chưa có
                if not p_info["age"] or not p_info["location"]:
                    age, loc = extract_age_and_location(sent, name)
                    if age and not p_info["age"]:
                        p_info["age"] = age
                    if loc and not p_info["location"]:
                        p_info["location"] = loc

                # Trích xuất tổ chức
                org = extract_organization(sent, name)
                if org:
                    p_info["organization"].add(org)

                # Trích xuất câu phát ngôn nếu trong câu có dấu ngoặc kép
                quotes = extract_quotes_from_sentence(sent)
                for q in quotes:
                    if q not in p_info["quotes"]:
                        p_info["quotes"].append(q)

    # ====== BƯỚC 4: LỌC CHỈ GIỮ CHÍNH TRỊ GIA ======
    # Chỉ giữ nhân vật có ít nhất 1 chức vụ hoặc tổ chức mang tính chính trị
    political_persons = {}
    filtered_count = 0
    for name, p_info in persons_map.items():
        if p_info["mention_count"] == 0:
            continue
        if is_politician(p_info["role_title"], p_info["organization"]):
            political_persons[name] = p_info
        else:
            filtered_count += 1

    # ====== BƯỚC 5: Chuẩn hóa đầu ra ======
    result_rows = []
    for name, p_info in political_persons.items():
        result_rows.append({
            "article_id": article.get("article_id"),
            "published_date": article.get("published_date"),
            "publisher": article.get("publisher", ""),
            "person_name": p_info["person_name"],
            "honorific": p_info["honorific"],
            "role_title": ", ".join(sorted(p_info["role_title"])),
            "organization": ", ".join(sorted(p_info["organization"])),
            "age": p_info["age"],
            "location": p_info["location"],
            "mention_count": p_info["mention_count"],
            "is_main_character": False,  # Sẽ cập nhật ở ngay bên dưới
            "quotes": p_info["quotes"],
            "actions_summary": " | ".join(p_info["actions_context"]),
            "article_title": article.get("title"),
            "article_url": article.get("baomoi_url", article.get("original_url", ""))
        })

    # Sắp xếp nhân vật theo số lần xuất hiện giảm dần và đánh dấu Nhân vật chính
    result_rows.sort(key=lambda x: x["mention_count"], reverse=True)
    if result_rows:
        result_rows[0]["is_main_character"] = True

    return result_rows


def save_to_sqlite(persons_rows: list[dict], db_path: str):
    """Lưu danh sách nhân vật chính trị vào bảng SQLite để dễ dàng truy vấn SQL."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Xóa bảng cũ nếu có để tránh trùng dữ liệu khi chạy lại
    cursor.execute("DROP TABLE IF EXISTS article_persons")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_persons (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT,
            published_date TEXT,
            publisher TEXT,
            person_name TEXT,
            honorific TEXT,
            role_title TEXT,
            organization TEXT,
            age INTEGER,
            location TEXT,
            mention_count INTEGER,
            is_main_character BOOLEAN,
            quotes TEXT,
            actions_summary TEXT,
            article_title TEXT,
            article_url TEXT
        )
    """)

    # Tạo Index trên cột person_name và article_id để tìm kiếm cực nhanh
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_name ON article_persons(person_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_id ON article_persons(article_id)")

    for row in persons_rows:
        cursor.execute("""
            INSERT INTO article_persons (
                article_id, published_date, publisher,
                person_name, honorific, role_title, organization,
                age, location, mention_count, is_main_character,
                quotes, actions_summary, article_title, article_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["article_id"], row["published_date"], row["publisher"],
            row["person_name"], row["honorific"], row["role_title"], row["organization"],
            row["age"], row["location"], row["mention_count"], 1 if row["is_main_character"] else 0,
            json.dumps(row["quotes"], ensure_ascii=False), row["actions_summary"],
            row["article_title"], row["article_url"]
        ))

    conn.commit()
    conn.close()


def main():
    if not os.path.exists(INPUT_ARTICLES_JSON):
        print(f"[!] Không tìm thấy file '{INPUT_ARTICLES_JSON}'. Hãy chạy script thu thập bài báo trước.")
        return

    # Đọc file JSONL (mỗi dòng là một JSON object)
    articles = []
    with open(INPUT_ARTICLES_JSON, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                articles.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[!] Lỗi parse JSON tại dòng {line_num}: {e}")

    print(f"[*] Đang phân tích và bóc tách CHÍNH TRỊ GIA từ {len(articles)} bài báo...")
    print(f"    (Chỉ giữ nhân vật có chức vụ/tổ chức chính trị Việt Nam)")
    all_person_records = []
    total_all_persons = 0
    total_politicians = 0

    for idx, article in enumerate(articles, start=1):
        extracted = extract_persons_from_article(article)
        all_person_records.extend(extracted)
        total_politicians += len(extracted)
        if idx % 200 == 0 or idx == len(articles):
            print(f"  -> Đã xử lý {idx}/{len(articles)} bài báo | "
                  f"Tìm thấy {len(all_person_records)} lượt chính trị gia.")

    # 1. Xuất ra file JSON chuẩn
    with open(OUTPUT_PERSONS_JSON, "w", encoding="utf-8") as f_out:
        json.dump(all_person_records, f_out, ensure_ascii=False, indent=2)

    # 2. Xuất ra Database SQLite
    save_to_sqlite(all_person_records, OUTPUT_SQLITE_DB)

    # 3. Xuất ra CSV (nếu có cài pandas) để mở xem trực tiếp trên Excel
    try:
        import pandas as pd
        df = pd.DataFrame(all_person_records)
        # Chuyển list quotes thành chuỗi trước khi lưu CSV
        df["quotes"] = df["quotes"].apply(lambda q: " ; ".join(q) if isinstance(q, list) else q)
        df.to_csv(OUTPUT_PERSONS_CSV, index=False, encoding="utf-8-sig")
        print(f"[+] Đã xuất bảng Excel/CSV tại: '{OUTPUT_PERSONS_CSV}'")
    except ImportError:
        pass

    print(f"\n[HOÀN TẤT] Đã lưu {len(all_person_records)} hồ sơ CHÍNH TRỊ GIA vào:")
    print(f"  - JSON: '{OUTPUT_PERSONS_JSON}'")
    print(f"  - SQLite: '{OUTPUT_SQLITE_DB}'")
    print(f"  - CSV: '{OUTPUT_PERSONS_CSV}'")


if __name__ == "__main__":
    main()