import json
import re
import sys
import sqlite3
import os
from collections import defaultdict, Counter
from itertools import combinations

# Fix encoding cho Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ================= CẤU HÌNH FILE =================
INPUT_ARTICLES_JSON = "baomoi_political_corpus.jsonl"           # File bài báo đầu vào
OUTPUT_PERSONS_JSON = "baomoi_persons_political_table.json"     # Bảng nhân vật - bài báo (JSON)
OUTPUT_PERSONS_CSV = "baomoi_persons_political_table.csv"       # Bảng nhân vật - bài báo (CSV/Excel)
OUTPUT_PROFILES_JSON = "baomoi_vn_politicians_profiles.json"    # Bảng hồ sơ tổng hợp Chính trị gia VN (Nodes đồ thị)
OUTPUT_PROFILES_CSV = "baomoi_vn_politicians_profiles.csv"      # Bảng hồ sơ tổng hợp Chính trị gia VN (CSV)
OUTPUT_EDGES_CSV = "baomoi_vn_politicians_edges.csv"            # Bảng cạnh quan hệ đồng xuất hiện (Edges đồ thị)
OUTPUT_SQLITE_DB = "baomoi_knowledge_graph1.db"                 # Cơ sở dữ liệu SQLite (3 bảng đồ thị)
# =================================================

# ============ 1. DANH SÁCH TỈNH / THÀNH PHỐ VIỆT NAM & CHUẨN HÓA ============
# Bao gồm cả 34 tỉnh/thành sau sáp nhập và 63 tỉnh/thành trước sáp nhập để bắt đầy đủ lịch sử công tác
PROVINCE_ALIASES = {
    "thành phố hồ chí minh": "TP.HCM",
    "tp hồ chí minh": "TP.HCM",
    "tp. hồ chí minh": "TP.HCM",
    "tp.hcm": "TP.HCM",
    "tphcm": "TP.HCM",
    "thành phố hà nội": "Hà Nội",
    "tp hà nội": "Hà Nội",
    "tp. hà nội": "Hà Nội",
    "thủ đô hà nội": "Hà Nội",
    "hà nội": "Hà Nội",
    "thành phố hải phòng": "Hải Phòng",
    "tp hải phòng": "Hải Phòng",
    "tp. hải phòng": "Hải Phòng",
    "hải phòng": "Hải Phòng",
    "thành phố đà nẵng": "Đà Nẵng",
    "tp đà nẵng": "Đà Nẵng",
    "tp. đà nẵng": "Đà Nẵng",
    "đà nẵng": "Đà Nẵng",
    "thành phố cần thơ": "Cần Thơ",
    "tp cần thơ": "Cần Thơ",
    "tp. cần thơ": "Cần Thơ",
    "cần thơ": "Cần Thơ",
    "thành phố huế": "Huế",
    "tp huế": "Huế",
    "tp. huế": "Huế",
    "thừa thiên huế": "Huế",
    "thừa thiên - huế": "Huế",
    "huế": "Huế",
    "bà rịa - vũng tàu": "Bà Rịa - Vũng Tàu",
    "bà rịa vũng tàu": "Bà Rịa - Vũng Tàu",
    "đắk lắk": "Đắk Lắk",
    "đắc lắc": "Đắk Lắk",
    "đắk nông": "Đắk Nông",
    "đắc nông": "Đắk Nông",
    "bắc kạn": "Bắc Kạn",
    "bắc cạn": "Bắc Kạn",
}

CANONICAL_PROVINCES = [
    "Hà Nội", "TP.HCM", "Hải Phòng", "Đà Nẵng", "Huế", "Cần Thơ",
    "An Giang", "Bà Rịa - Vũng Tàu", "Bạc Liêu", "Bắc Giang", "Bắc Kạn", "Bắc Ninh",
    "Bến Tre", "Bình Dương", "Bình Định", "Bình Phước", "Bình Thuận", "Cà Mau",
    "Cao Bằng", "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp",
    "Gia Lai", "Hà Giang", "Hà Nam", "Hà Tĩnh", "Hải Dương", "Hậu Giang",
    "Hòa Bình", "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu",
    "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", "Nghệ An",
    "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên", "Quảng Bình", "Quảng Nam",
    "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sóc Trăng", "Sơn La", "Tây Ninh",
    "Thái Bình", "Thái Nguyên", "Thanh Hóa", "Tiền Giang", "Trà Vinh", "Tuyên Quang",
    "Vĩnh Long", "Vĩnh Phúc", "Yên Bái",
]

for _p in CANONICAL_PROVINCES:
    if _p.lower() not in PROVINCE_ALIASES:
        PROVINCE_ALIASES[_p.lower()] = _p

# Sắp xếp giảm dần theo độ dài để ưu tiên khớp cụm dài trước (VD: "Bà Rịa - Vũng Tàu", "Thành phố Hồ Chí Minh")
SORTED_PROVINCE_KEYS = sorted(PROVINCE_ALIASES.keys(), key=len, reverse=True)
PROVINCE_REGEX_STR = "|".join(re.escape(k) for k in SORTED_PROVINCE_KEYS)
PROVINCE_PATTERN = re.compile(rf"(?<!\w)({PROVINCE_REGEX_STR})(?!\w)", re.IGNORECASE)

# ============ 2. TỪ ĐIỂN HỌ NGƯỜI VIỆT (KINH & DÂN TỘC THIỂU SỐ) ============
VN_SURNAMES = {
    # Họ phổ biến và truyền thống của người Việt
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
    "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đoàn", "Vương", "Trịnh",
    "Đinh", "Lâm", "Phùng", "Mai", "Tạ", "Cao", "Hà", "Chu", "Trương", "Châu",
    "Tống", "Thái", "Tăng", "Lưu", "Kiều", "Nghiêm", "Lại", "Đàm", "Mạc", "Từ",
    "Quách", "Triệu", "La", "Lã", "Uông", "Văn", "Khúc", "Biện", "Dư", "Sử",
    "Tiêu", "Giang", "Quản", "Thân", "Cù", "Khuất", "Tô", "Lương", "Tào", "Doãn",
    "Đồng", "Bạch", "Bành", "Chung", "Đậu", "Đường", "Hàn", "Hình", "Hứa", "Khổng",
    "Kim", "Lãnh", "Liễu", "Lỗ", "Lư", "Mã", "Mạnh", "Ninh", "Nhâm", "Nhữ",
    "Phí", "Phó", "Phương", "Quang", "Tôn", "Tưởng", "Viên", "Ngụy", "Ngọ", "Giáp",
    "Âu", "Trừ", "Đắc", "Duy", "Hồng",
    # Họ & tiền tố tên các dân tộc thiểu số Việt Nam trong hệ thống chính trị
    "Nông", "Vi", "Lò", "Lường", "Lục", "Bàn", "Hầu", "Giàng", "Sùng", "Mùa",
    "Vàng", "Thào", "Chảo", "Tẩn", "Phàn", "Chau", "Danh", "Kiên", "Sơn", "Thạch",
    "Y", "Rơ", "Ksor", "Kpă", "Nay", "Siu", "Cầm", "Sa", "Lữ", "Kha", "Moong",
    "Điểu", "Cil", "Briư", "A", "Ma", "Lèng", "Vừ", "Tráng", "Lầu", "Sình",
    "Cứ", "Hờ", "Pờ", "Tòng", "Quàng", "Bế", "Lăng", "Đèo", "Nùng",
}

# Họ rất mạnh dùng để cho phép tên 2 âm tiết (VD: Tô Lâm, Lương Cường, Lê Quân, Mai Hoàng, Hoàng Nam, Đào Mỹ...)
CORE_TWO_WORD_SURNAMES = {
    "Tô", "Lương", "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan",
    "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đoàn",
    "Vương", "Trịnh", "Đinh", "Lâm", "Phùng", "Mai", "Tạ", "Cao", "Hà", "Chu",
    "Trương", "Châu", "Tống", "Thái", "Nông", "Vi", "Lò", "Hầu", "Giàng", "Sùng",
    "Y", "Sơn", "Cil", "Ksor",
}

# Các âm tiết đặc thù của người dân tộc thiểu số Tây Nguyên / miền núi phía Bắc
ETHNIC_SYLLABLE_ALLOWLIST = {
    "ksor", "kđăm", "tơr", "k'mak", "k'ré", "h'phik", "niê", "cil", "bri", "briư",
    "páo", "lềnh", "mỷ", "vảng", "chăm", "kpă", "siu", "y", "a", "h'ra", "mlô",
    "hwing", "knul", "byă", "krông", "êban", "hđơk",
}

# ============ 3. DANH SÁCH LOẠI TRỪ: QUỐC GIA, CHÍNH TRỊ GIA QUỐC TẾ, TỪ KHÔNG PHẢI NGƯỜI ============
FOREIGN_COUNTRIES = [
    "Trung Quốc", "Mỹ", "Hoa Kỳ", "Nga", "Liên bang Nga", "Lào", "Campuchia", "Cuba",
    "Triều Tiên", "Hàn Quốc", "Nhật Bản", "Singapore", "Thái Lan", "Malaysia", "Indonesia",
    "Philippines", "Ấn Độ", "Australia", "Úc", "New Zealand", "Pháp", "Đức", "Anh",
    "Vương quốc Anh", "Italy", "Ý", "Hungary", "Tây Ban Nha", "Bồ Đào Nha", "Thụy Sĩ",
    "Thụy Điển", "Phần Lan", "Na Uy", "Đan Mạch", "Hà Lan", "Bỉ", "Áo", "Ba Lan",
    "Séc", "Slovakia", "Romania", "Bulgaria", "Belarus", "Ukraine", "Thổ Nhĩ Kỳ",
    "Israel", "Palestine", "Iran", "Iraq", "Syria", "Lebanon", "Ai Cập", "Nam Phi",
    "Brazil", "Argentina", "Mexico", "Canada", "Venezuela", "Chile", "Peru", "Panama",
    "Suriname", "Mông Cổ", "Kazakhstan", "Uzbekistan", "Azerbaijan", "Armenia",
    "Ả Rập Xê Út", "UAE", "Qatar", "Kuwait", "Đài Loan", "Hồng Kông",
    "Liên Hợp Quốc", "Liên hợp quốc", "ASEAN", "EU", "Châu Âu", "NATO", "G7", "G20",
]
FOREIGN_COUNTRY_REGEX = re.compile(
    r"(?<!\w)(" + "|".join(re.escape(c) for c in sorted(FOREIGN_COUNTRIES, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE
)

# Chính trị gia nước ngoài có tên phiên âm Hán-Việt hoặc hay xuất hiện trong báo Việt Nam
BLACKLIST_PERSONS = {
    # Lãnh đạo / quan chức Trung Quốc, Singapore, Triều Tiên phiên âm Hán Việt
    "tập cận bình", "lý cường", "vương nghị", "triệu lạc tế", "vương hỗ ninh",
    "thái kỳ", "đinh tiết tường", "lý hi", "hạ vinh", "mao ninh", "lâm kiếm",
    "hồ cẩm đào", "giang trạch dân", "chu dung cơ", "ôn gia bảo", "lý khắc cường",
    "dương khiết trì", "lưu kiến siêu", "tần cương", "đổng quân", "trương hựu hiệp",
    "hà vệ đông", "vương tiểu hồng", "trần văn thanh", "hàn chính", "lý hiển long",
    "hoàng tuần tài", "lý quang diệu", "kim nhật thành", "kim chính nhật", "kim chính ân",
    # Lãnh tụ / nhân vật lịch sử hoặc địa danh trùng tên (tránh nhiễu đồ thị đương đại)
    "hồ chí minh", "tôn đức thắng", "lê duẩn", "trường chinh", "phạm văn đồng",
    "võ nguyên giáp", "võ văn kiệt", "võ chí công", "nguyễn văn linh", "đỗ mười",
    "lê khả phiêu", "phạm hùng", "huỳnh tấn phát", "nguyễn hữu thọ", "phan đình phùng",
    "hoàng hoa thám", "nguyễn thái học", "tôn thất tùng", "trần đại nghĩa",
    # Các cụm từ cơ quan/địa danh 2-3 từ dễ bị nhầm
    "nhà trắng", "biển đông", "tây nguyên", "đồng bằng", "trung ương", "quốc hội",
    "chính phủ", "nhà nước", "mặt trận", "tổ quốc", "cộng sản", "nhân dân",
    "quân đội", "công an", "biên phòng", "cảnh sát", "kiểm sát", "tòa án",
    "thanh tra", "kiểm toán", "thống kê", "hải quan", "kho bạc", "ngân hàng",
    "bảo hiểm", "xã hội", "thương binh", "liệt sĩ", "phụ nữ", "thanh niên",
    "nông dân", "lao động", "công đoàn", "sinh viên", "chiến dịch",
    "phú bình", "bảo ái", "nha bích", "quế sơn", "tây mỗ", "xuân phương",
    "ô chợ dừa", "giảng võ", "cầu giấy", "long thành", "kim liên", "phong thổ",
    "sơn hồng", "thục phán", "bạch thông", "vân phú", "vĩnh thành", "cửa nam",
    "vinh phú", "đức xuân", "tam tiến", "tam quang", "bồ bản", "vũ lăng",
    "bạch đằng", "trường hà", "pác bó", "đất mũi", "mường thanh",
}

# Các từ KHÔNG BAO GIỜ nằm trong tên người Việt (tổ chức, chức danh, địa danh hành chính)
NON_NAME_SYLLABLES = {
    "bộ", "sở", "ban", "ngành", "cục", "vụ", "viện", "trường", "phòng", "khoa",
    "đảng", "ủy", "tỉnh", "thành", "huyện", "quận", "xã", "phường", "thôn", "bản", "ấp",
    "khối", "đoàn", "hội", "đội", "nhóm", "liên", "tổng", "chi", "cơ", "quan",
    "quốc", "chính", "phủ", "nhà", "nước", "mặt", "trận", "trung", "ương",
    "thường", "trực", "vụ", "chấp", "hành", "bí", "thư", "chủ", "tịch", "nhiệm",
    "trưởng", "phó", "giám", "đốc", "chánh", "án", "kiểm", "sát", "thanh", "tra",
    "toán", "tư", "lệnh", "huy", "tham", "mưu", "tướng", "tá", "úy", "sĩ",
    "đại", "thượng", "thiếu", "chuẩn", "đô", "cựu", "nguyên", "quyền",
    "ông", "bà", "anh", "chị", "em", "bác", "chú", "cô", "đồng", "chí",
    "công", "thương", "tài", "nội", "ngoại", "giao", "quốc", "xây", "dựng",
    "y", "tế", "giáo", "dục", "đào", "tạo", "nông", "nghiệp", "môi", "trường",
    "khoa", "học", "nghệ", "văn", "hóa", "thể", "thao", "du", "lịch", "dân", "tộc", "tôn",
    "thông", "tin", "truyền", "kế", "hoạch", "đầu", "lao", "động", "xã", "hội",
    "ngân", "hàng", "kho", "bạc", "thuế", "quan", "thống", "kê", "bảo", "hiểm",
    "tập", "cty", "clb", "ubnd", "hđnd", "mttq", "tw", "tƯ", "tp", "tphcm",
    "việt", "nam", "lào", "mỹ", "nga", "pháp", "đức", "nhật", "hàn", "ấn", "úc",
}

# Các từ không được phép xuất hiện trong tên 2 âm tiết (tránh bắt nhầm cụm danh từ 2 từ viết hoa)
TWO_WORD_FORBIDDEN_SECOND_SYLLABLES = {
    "ủy", "bộ", "đảng", "đoàn", "hội", "sở", "ban", "cục", "vụ", "viện", "phòng",
    "tỉnh", "thành", "huyện", "quận", "xã", "phường", "trưởng", "phó", "tịch", "thư",
    "cộng", "nhân", "quốc", "chính", "trung", "ương", "tác", "pháp", "tài", "kế",
    "khoa", "phát", "kinh", "thanh", "tổng", "các", "địa", "thông", "quản", "chức",
    "an", "nội", "ngoại", "thương", "xây", "y", "giáo", "nông", "văn", "dân", "lao",
}

# Regex kiểm tra âm tiết tiếng Việt chuẩn (không chứa f, j, w, z; phụ âm đầu & phụ âm cuối hợp lệ)
VN_VOWELS = "aàáạảãăằắặẳẵâầấậẩẫeèéẹẻẽêềếệểễiìíịỉĩoòóọỏõôồốộổỗơờớợởỡuùúụủũưừứựửữyỳýỵỷỹ"
VN_INITIAL_CONSONANTS = r"(?:ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|[bcdđghklmnpqrstvx])?"
VN_FINAL_CONSONANTS = r"(?:ch|ng|nh|[cmnpt])?"
VN_SYLLABLE_REGEX = re.compile(
    rf"^{VN_INITIAL_CONSONANTS}[{VN_VOWELS}]{{1,3}}{VN_FINAL_CONSONANTS}$",
    re.IGNORECASE
)


def is_valid_vn_syllable(word: str) -> bool:
    """Kiểm tra 1 từ có phải là âm tiết tiếng Việt (hoặc dân tộc thiểu số VN) hợp lệ."""
    w_low = word.lower().strip()
    if not w_low:
        return False
    if w_low in ETHNIC_SYLLABLE_ALLOWLIST:
        return True
    # Không chứa ký tự Latin ngoài bảng chữ cái tiếng Việt
    if any(ch in w_low for ch in "fjwz0123456789"):
        return False
    return bool(VN_SYLLABLE_REGEX.match(w_low))


def is_valid_vn_politician_name(name: str) -> bool:
    """
    Kiểm tra nghiêm ngặt xem chuỗi có phải là tên Chính trị gia Việt Nam hợp lệ:
    - Độ dài 2 đến 5 từ, mỗi từ viết hoa chữ cái đầu, phần còn lại viết thường
    - Âm tiết chuẩn tiếng Việt (loại bỏ hoàn toàn tên tiếng Anh, Nga, Lào, Campuchia, Nhật...)
    - Từ đầu tiên phải nằm trong từ điển Họ người Việt (VN_SURNAMES)
    - Không nằm trong danh sách đen (cơ quan, địa danh, chính trị gia Trung Quốc phiên âm, nhân vật lịch sử)
    """
    if not name:
        return False
    name = " ".join(name.split())
    name_low = name.lower()

    if name_low in BLACKLIST_PERSONS or name_low in PROVINCE_ALIASES:
        return False
    if FOREIGN_COUNTRY_REGEX.search(name):
        return False

    words = name.split()
    if len(words) < 2 or len(words) > 5:
        return False

    # Kiểm tra họ (từ đầu tiên)
    first_word = words[0]
    if first_word not in VN_SURNAMES:
        return False

    # Kiểm tra từng từ trong tên
    for w in words:
        if not w[0].isupper():
            return False
        # Loại bỏ từ viết hoa toàn bộ >= 2 ký tự (viết tắt như UBND, HĐND, MTTQ, TPHCM...)
        if len(w) >= 2 and w.isupper():
            return False
        if not is_valid_vn_syllable(w):
            return False

    # Không cho phép các từ khóa chức vụ/tổ chức xuất hiện ở đầu hoặc cuối tên
    # (Lưu ý: một số từ như Thanh, Văn, Quốc, Chính, Nội... có thể là tên đệm/tên riêng,
    # nhưng các từ như Đảng, Bộ, Sở, Ban, Cục, Vụ, Viện, Tỉnh, Thành, Huyện, Xã, Phường, Ủy, Trưởng, Phó, Bí, Tịch... thì tuyệt đối cấm)
    STRICT_NON_NAME_WORDS = {
        "bộ", "sở", "ban", "ngành", "cục", "vụ", "viện", "phòng", "đảng", "ủy",
        "tỉnh", "thành", "huyện", "quận", "xã", "phường", "thôn", "bản", "khối",
        "đoàn", "hội", "nhóm", "tổng", "chi", "chính", "phủ", "mặt", "trận",
        "ương", "trực", "chấp", "bí", "tịch", "nhiệm", "trưởng", "phó", "giám",
        "đốc", "chánh", "kiểm", "sát", "tra", "toán", "lệnh", "tướng", "tá",
        "cựu", "nguyên", "ông", "bà", "chị", "anh", "đồng", "chí", "thương",
        "nội", "ngoại", "xây", "dựng", "tế", "giáo", "dục", "đào", "tạo", "môi",
        "nghệ", "thể", "thao", "du", "lịch", "tộc", "truyền", "hoạch", "đầu",
        "lao", "động", "ngân", "hàng", "bạc", "thuế", "thống", "kê", "hiểm", "tập",
    }
    if words[0].lower() in STRICT_NON_NAME_WORDS or words[-1].lower() in STRICT_NON_NAME_WORDS:
        return False
    for w in words[1:]:
        if w.lower() in {"đảng", "bộ", "sở", "ban", "cục", "vụ", "tỉnh", "huyện", "quận", "xã", "phường", "ủy", "trưởng", "phó", "tịch", "nhiệm", "giám", "đốc", "tướng", "tá", "ông", "bà"}:
            return False

    # Nếu tên chỉ có 2 từ: kiểm tra chặt hơn để tránh bắt nhầm cụm danh từ 2 từ
    if len(words) == 2:
        if first_word not in CORE_TWO_WORD_SURNAMES:
            return False
        if words[1].lower() in TWO_WORD_FORBIDDEN_SECOND_SYLLABLES:
            return False
        if words[1].lower() in STRICT_NON_NAME_WORDS:
            return False

    return True


# ============ 4. DANH MỤC HỆ THỐNG CHÍNH TRỊ VN: CHỨC VỤ, BAN NGÀNH, CƠ QUAN ============

# Danh xưng & học hàm học vị
HONORIFICS = ["đồng chí", "ông", "bà"]
ACADEMIC_RANKS = [
    "gs.ts.kts", "gs.ts", "pgs.ts", "ts.bs", "ths.bs", "ts", "ths", "bs", "kts",
    "giáo sư, tiến sĩ", "phó giáo sư, tiến sĩ", "giáo sư", "phó giáo sư", "tiến sĩ", "thạc sĩ",
]

# Quân hàm / Cấp bậc LLVT
MILITARY_POLICE_RANKS = [
    "đại tướng", "thượng tướng", "trung tướng", "thiếu tướng",
    "đô đốc", "phó đô đốc", "chuẩn đô đốc",
    "đại tá", "thượng tá", "trung tá", "thiếu tá",
]

# Danh sách 14 Bộ (sau hợp nhất), các Bộ tên cũ, và 3 Cơ quan ngang Bộ + ánh xạ sang Ngành
MINISTRY_MAP = {
    "bộ quốc phòng": ("Bộ Quốc phòng", "Ngành Quốc phòng"),
    "bộ công an": ("Bộ Công an", "Ngành Công an"),
    "bộ ngoại giao": ("Bộ Ngoại giao", "Ngành Ngoại giao"),
    "bộ nội vụ": ("Bộ Nội vụ", "Ngành Nội vụ"),
    "bộ tư pháp": ("Bộ Tư pháp", "Ngành Tư pháp"),
    "bộ tài chính": ("Bộ Tài chính", "Ngành Tài chính"),
    "bộ công thương": ("Bộ Công Thương", "Ngành Công Thương"),
    "bộ nông nghiệp và môi trường": ("Bộ Nông nghiệp và Môi trường", "Ngành Nông nghiệp và Môi trường"),
    "bộ nn&mt": ("Bộ Nông nghiệp và Môi trường", "Ngành Nông nghiệp và Môi trường"),
    "bộ nn-mt": ("Bộ Nông nghiệp và Môi trường", "Ngành Nông nghiệp và Môi trường"),
    "bộ xây dựng": ("Bộ Xây dựng", "Ngành Xây dựng"),
    "bộ văn hóa, thể thao và du lịch": ("Bộ Văn hóa, Thể thao và Du lịch", "Ngành Văn hóa, Thể thao và Du lịch"),
    "bộ văn hóa - thể thao và du lịch": ("Bộ Văn hóa, Thể thao và Du lịch", "Ngành Văn hóa, Thể thao và Du lịch"),
    "bộ vhttdl": ("Bộ Văn hóa, Thể thao và Du lịch", "Ngành Văn hóa, Thể thao và Du lịch"),
    "bộ vh,tt&dl": ("Bộ Văn hóa, Thể thao và Du lịch", "Ngành Văn hóa, Thể thao và Du lịch"),
    "bộ vh-tt-dl": ("Bộ Văn hóa, Thể thao và Du lịch", "Ngành Văn hóa, Thể thao và Du lịch"),
    "bộ khoa học và công nghệ": ("Bộ Khoa học và Công nghệ", "Ngành Khoa học và Công nghệ"),
    "bộ kh&cn": ("Bộ Khoa học và Công nghệ", "Ngành Khoa học và Công nghệ"),
    "bộ kh-cn": ("Bộ Khoa học và Công nghệ", "Ngành Khoa học và Công nghệ"),
    "bộ giáo dục và đào tạo": ("Bộ Giáo dục và Đào tạo", "Ngành Giáo dục và Đào tạo"),
    "bộ gd&đt": ("Bộ Giáo dục và Đào tạo", "Ngành Giáo dục và Đào tạo"),
    "bộ gd-đt": ("Bộ Giáo dục và Đào tạo", "Ngành Giáo dục và Đào tạo"),
    "bộ y tế": ("Bộ Y tế", "Ngành Y tế"),
    "bộ dân tộc và tôn giáo": ("Bộ Dân tộc và Tôn giáo", "Ngành Dân tộc và Tôn giáo"),
    # Tên các Bộ trước hợp nhất (lịch sử công tác)
    "bộ kế hoạch và đầu tư": ("Bộ Kế hoạch và Đầu tư", "Ngành Kế hoạch và Đầu tư"),
    "bộ kh&đt": ("Bộ Kế hoạch và Đầu tư", "Ngành Kế hoạch và Đầu tư"),
    "bộ giao thông vận tải": ("Bộ Giao thông vận tải", "Ngành Giao thông vận tải"),
    "bộ gtvt": ("Bộ Giao thông vận tải", "Ngành Giao thông vận tải"),
    "bộ tài nguyên và môi trường": ("Bộ Tài nguyên và Môi trường", "Ngành Tài nguyên và Môi trường"),
    "bộ tn&mt": ("Bộ Tài nguyên và Môi trường", "Ngành Tài nguyên và Môi trường"),
    "bộ nông nghiệp và phát triển nông thôn": ("Bộ Nông nghiệp và Phát triển nông thôn", "Ngành Nông nghiệp và Phát triển nông thôn"),
    "bộ nn&ptnt": ("Bộ Nông nghiệp và Phát triển nông thôn", "Ngành Nông nghiệp và Phát triển nông thôn"),
    "bộ thông tin và truyền thông": ("Bộ Thông tin và Truyền thông", "Ngành Thông tin và Truyền thông"),
    "bộ tt&tt": ("Bộ Thông tin và Truyền thông", "Ngành Thông tin và Truyền thông"),
    "bộ lao động - thương binh và xã hội": ("Bộ Lao động - Thương binh và Xã hội", "Ngành Lao động - Thương binh và Xã hội"),
    "bộ lao động, thương binh và xã hội": ("Bộ Lao động - Thương binh và Xã hội", "Ngành Lao động - Thương binh và Xã hội"),
    "bộ lđ-tb&xh": ("Bộ Lao động - Thương binh và Xã hội", "Ngành Lao động - Thương binh và Xã hội"),
    "bộ lđ,tb&xh": ("Bộ Lao động - Thương binh và Xã hội", "Ngành Lao động - Thương binh và Xã hội"),
    # Cơ quan ngang Bộ & cơ quan TW
    "văn phòng chính phủ": ("Văn phòng Chính phủ", "Văn phòng Chính phủ"),
    "thanh tra chính phủ": ("Thanh tra Chính phủ", "Ngành Thanh tra"),
    "ngân hàng nhà nước việt nam": ("Ngân hàng Nhà nước Việt Nam", "Ngành Ngân hàng"),
    "ngân hàng nhà nước": ("Ngân hàng Nhà nước Việt Nam", "Ngành Ngân hàng"),
    "kiểm toán nhà nước": ("Kiểm toán Nhà nước", "Ngành Kiểm toán"),
    "tòa án nhân dân tối cao": ("Tòa án nhân dân tối cao", "Ngành Tòa án"),
    "tand tối cao": ("Tòa án nhân dân tối cao", "Ngành Tòa án"),
    "viện kiểm sát nhân dân tối cao": ("Viện kiểm sát nhân dân tối cao", "Ngành Kiểm sát"),
    "vksnd tối cao": ("Viện kiểm sát nhân dân tối cao", "Ngành Kiểm sát"),
    "ủy ban dân tộc": ("Ủy ban Dân tộc", "Ngành Dân tộc và Tôn giáo"),
}

# Các Ban Đảng Trung ương & Đảng ủy trực thuộc TW
CENTRAL_PARTY_DEPTS = {
    "ban tổ chức trung ương": ("Ban Tổ chức Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban tổ chức tw": ("Ban Tổ chức Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ủy ban kiểm tra trung ương": ("Ủy ban Kiểm tra Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ủy ban kiểm tra tw": ("Ủy ban Kiểm tra Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban tuyên giáo và dân vận trung ương": ("Ban Tuyên giáo và Dân vận Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban tuyên giáo và dân vận tw": ("Ban Tuyên giáo và Dân vận Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban tuyên giáo trung ương": ("Ban Tuyên giáo Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban tuyên giáo tw": ("Ban Tuyên giáo Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban dân vận trung ương": ("Ban Dân vận Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban dân vận tw": ("Ban Dân vận Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban nội chính trung ương": ("Ban Nội chính Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban nội chính tw": ("Ban Nội chính Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban chính sách, chiến lược trung ương": ("Ban Chính sách, chiến lược Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban chính sách chiến lược trung ương": ("Ban Chính sách, chiến lược Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban kinh tế trung ương": ("Ban Kinh tế Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban kinh tế tw": ("Ban Kinh tế Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "ban đối ngoại trung ương": ("Ban Đối ngoại Trung ương", "Ban Chấp hành Trung ương Đảng"),
    "văn phòng trung ương đảng": ("Văn phòng Trung ương Đảng", "Ban Chấp hành Trung ương Đảng"),
    "văn phòng trung ương": ("Văn phòng Trung ương Đảng", "Ban Chấp hành Trung ương Đảng"),
    "học viện chính trị quốc gia hồ chí minh": ("Học viện Chính trị quốc gia Hồ Chí Minh", "Học viện Chính trị quốc gia Hồ Chí Minh"),
    "hội đồng lý luận trung ương": ("Hội đồng Lý luận Trung ương", "Hội đồng Lý luận Trung ương"),
    "báo nhân dân": ("Báo Nhân Dân", "Báo Nhân Dân"),
    "tạp chí cộng sản": ("Tạp chí Cộng sản", "Tạp chí Cộng sản"),
    "đảng ủy các cơ quan đảng trung ương": ("Khối Đảng Trung ương", "Đảng ủy các cơ quan Đảng Trung ương"),
    "đảng ủy chính phủ": ("Khối Chính phủ", "Đảng ủy Chính phủ"),
    "đảng ủy quốc hội": ("Khối Quốc hội", "Đảng ủy Quốc hội"),
    "đảng ủy mặt trận tổ quốc, các đoàn thể trung ương": ("Khối Mặt trận - Đoàn thể", "Đảng ủy Mặt trận Tổ quốc, các đoàn thể Trung ương"),
    "quân ủy trung ương": ("Ngành Quốc phòng", "Quân ủy Trung ương"),
    "đảng ủy công an trung ương": ("Ngành Công an", "Đảng ủy Công an Trung ương"),
}

# Các Ủy ban của Quốc hội & Văn phòng Chủ tịch nước, Văn phòng Quốc hội
NATIONAL_ASSEMBLY_COMMITTEES = {
    "hội đồng dân tộc": "Hội đồng Dân tộc của Quốc hội",
    "ủy ban pháp luật và tư pháp": "Ủy ban Pháp luật và Tư pháp của Quốc hội",
    "ủy ban pháp luật": "Ủy ban Pháp luật của Quốc hội",
    "ủy ban tư pháp": "Ủy ban Tư pháp của Quốc hội",
    "ủy ban kinh tế và tài chính": "Ủy ban Kinh tế và Tài chính của Quốc hội",
    "ủy ban kinh tế": "Ủy ban Kinh tế của Quốc hội",
    "ủy ban tài chính - ngân sách": "Ủy ban Tài chính - Ngân sách của Quốc hội",
    "ủy ban tài chính, ngân sách": "Ủy ban Tài chính - Ngân sách của Quốc hội",
    "ủy ban quốc phòng, an ninh và đối ngoại": "Ủy ban Quốc phòng, An ninh và Đối ngoại của Quốc hội",
    "ủy ban quốc phòng và an ninh": "Ủy ban Quốc phòng và An ninh của Quốc hội",
    "ủy ban đối ngoại": "Ủy ban Đối ngoại của Quốc hội",
    "ủy ban văn hóa và xã hội": "Ủy ban Văn hóa và Xã hội của Quốc hội",
    "ủy ban văn hóa, giáo dục": "Ủy ban Văn hóa, Giáo dục của Quốc hội",
    "ủy ban xã hội": "Ủy ban Xã hội của Quốc hội",
    "ủy ban khoa học, công nghệ và môi trường": "Ủy ban Khoa học, Công nghệ và Môi trường của Quốc hội",
    "ủy ban công tác đại biểu": "Ủy ban Công tác đại biểu của Quốc hội",
    "ban công tác đại biểu": "Ban Công tác đại biểu thuộc UBTV Quốc hội",
    "ủy ban dân nguyện và giám sát": "Ủy ban Dân nguyện và Giám sát của Quốc hội",
    "ban dân nguyện": "Ban Dân nguyện thuộc UBTV Quốc hội",
    "văn phòng quốc hội": "Văn phòng Quốc hội",
    "văn phòng chủ tịch nước": "Văn phòng Chủ tịch nước",
}

# Danh sách Sở chuyên môn địa phương
PROVINCIAL_DEPT_NAMES = [
    "Sở Văn hóa, Thể thao và Du lịch",
    "Sở Văn hóa - Thể thao và Du lịch",
    "Sở Văn hóa và Thể thao",
    "Sở Nông nghiệp và Môi trường",
    "Sở Nông nghiệp và Phát triển nông thôn",
    "Sở Tài nguyên và Môi trường",
    "Sở Khoa học và Công nghệ",
    "Sở Thông tin và Truyền thông",
    "Sở Giáo dục và Đào tạo",
    "Sở Lao động - Thương binh và Xã hội",
    "Sở Kế hoạch và Đầu tư",
    "Sở Giao thông vận tải",
    "Sở Quy hoạch - Kiến trúc",
    "Sở Dân tộc và Tôn giáo",
    "Sở An toàn thực phẩm",
    "Sở Tài chính",
    "Sở Xây dựng",
    "Sở Nội vụ",
    "Sở Y tế",
    "Sở Công Thương",
    "Sở Du lịch",
    "Sở Tư pháp",
    "Sở Ngoại vụ",
]


def extract_provinces_from_text(text: str) -> list[str]:
    """Trích xuất tất cả tên tỉnh/thành phố xuất hiện trong đoạn văn bản và chuẩn hóa."""
    if not text:
        return []
    found = []
    for m in PROVINCE_PATTERN.finditer(text):
        raw_p = m.group(1).lower()
        # Tránh bắt "Chủ tịch Hồ Chí Minh", "đường Hồ Chí Minh", "tư tưởng Hồ Chí Minh", "Học viện ... Hồ Chí Minh"
        if raw_p in ("tp hồ chí minh", "tp. hồ chí minh", "thành phố hồ chí minh", "tp.hcm", "tphcm"):
            canon = "TP.HCM"
        else:
            canon = PROVINCE_ALIASES.get(raw_p)
        if canon and canon not in found:
            found.append(canon)
    return found


def protect_compound_commas(text: str) -> str:
    """
    Thay dấu phẩy nằm bên trong tên cố định của các Bộ/Ủy ban/Ban/Sở bằng ký tự tạm '§'
    để khi tách chuỗi chức vụ theo dấu phẩy không làm đứt gãy tên cơ quan.
    """
    compound_phrases = [
        "Bộ Văn hóa, Thể thao và Du lịch",
        "Sở Văn hóa, Thể thao và Du lịch",
        "Ủy ban Quốc phòng, An ninh và Đối ngoại",
        "Ủy ban Khoa học, Công nghệ và Môi trường",
        "Ủy ban Văn hóa, Giáo dục",
        "Ủy ban Tài chính, Ngân sách",
        "Ban Chính sách, chiến lược Trung ương",
        "Đảng ủy Mặt trận Tổ quốc, các đoàn thể Trung ương",
        "Bộ Lao động, Thương binh và Xã hội",
        "Sở Lao động, Thương binh và Xã hội",
        "tìm kiếm, quy tập và xác định danh tính hài cốt liệt sĩ",
        "phòng, chống tham nhũng, lãng phí, tiêu cực",
        "phòng, chống tham nhũng, tiêu cực",
        "phòng, chống ma túy và tội phạm",
        "phòng, chống tội phạm sử dụng công nghệ cao",
        "Giáo sư, Tiến sĩ",
        "Phó Giáo sư, Tiến sĩ",
    ]
    res = text
    for phrase in compound_phrases:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        res = pattern.sub(lambda m: m.group(0).replace(",", "§"), res)
    return res


def restore_compound_commas(text: str) -> str:
    return text.replace("§", ",")


# ============ 5. HÀM PHÂN TÍCH MỘT CỤM CHỨC VỤ -> (CHỨC VỤ, BAN NGÀNH, CƠ QUAN, TỈNH THÀNH) ============

def parse_political_clause(clause: str, fallback_province: str = "") -> dict:
    """
    Phân tích một mệnh đề chức danh (VD: "Thứ trưởng Bộ Nông nghiệp và Môi trường",
    "Chánh Văn phòng Ban Nội chính Thành ủy Hà Nội", "Ủy viên Bộ Chính trị, Bí thư Thành ủy Đà Nẵng")
    thành 4 thành phần chuẩn hóa:
      - roles: set[str] (Chức vụ)
      - ban_nganh: set[str] (Ban ngành / Sở / Cục / Vụ / Ủy ban / Lĩnh vực)
      - organizations: set[str] (Cơ quan / Bộ / Tỉnh ủy / Thành ủy / UBND / HĐND / Quân khu...)
      - provinces: set[str] (Tỉnh thành)
    """
    roles = set()
    ban_nganh = set()
    organizations = set()
    provinces = set()

    if not clause:
        return {"roles": roles, "ban_nganh": ban_nganh, "organizations": organizations, "provinces": provinces}

    c_clean = restore_compound_commas(clause).strip(" ,.;:-–—()[]\"'“”")
    # Cắt bỏ phần đuôi hành động nếu còn sót
    c_clean = re.split(
        r"\b(?:đã\s+|vừa\s+|đang\s+|sẽ\s+|cùng\s+|đồng\s+chủ\s+trì|chủ\s+trì|phát\s+biểu|nhấn\s+mạnh|"
        r"cho\s+biết|khẳng\s+định|yêu\s+cầu|đề\s+nghị|trình\s+bày|ký\s+ban\s+hành|ký\s+quyết\s+định|"
        r"ký\s+nghị\s+quyết|dự\s+và|tham\s+dự|tiếp\s+đoàn|tiếp\s+tục|làm\s+việc|đánh\s+giá|ghi\s+nhận|"
        r"biểu\s+dương|lưu\s+ý|bày\s+tỏ|gửi\s+lời|trao\s+quyết\s+định|trao\s+tặng|nêu\s+rõ|cho\s+rằng|"
        r"chia\s+sẻ|thông\s+tin|giải\s+trình|thừa\s+nhận|kết\s+luận|chỉ\s+đạo)\b",
        c_clean, flags=re.IGNORECASE
    )[0].strip(" ,.;:-–—()[]")

    if not c_clean:
        return {"roles": roles, "ban_nganh": ban_nganh, "organizations": organizations, "provinces": provinces}

    c_low = c_clean.lower()

    # Loại bỏ các chức danh thuần doanh nghiệp tư nhân (HĐQT, Tổng giám đốc công ty cổ phần...)
    if any(k in c_low for k in ["hội đồng quản trị", "hđqt", "công ty cổ phần", "tập đoàn mường thanh", "tập đoàn vạn thịnh phát"]):
        return {"roles": roles, "ban_nganh": ban_nganh, "organizations": organizations, "provinces": provinces}

    # 1. Trích xuất Tỉnh / Thành phố trong cụm
    clause_provinces = extract_provinces_from_text(c_clean)
    for p in clause_provinces:
        provinces.add(p)
    active_prov = clause_provinces[0] if clause_provinces else fallback_province

    # 2. Quân hàm / Cấp bậc Công an - Quân đội
    for rank in MILITARY_POLICE_RANKS:
        if re.search(rf"(?<!\w){re.escape(rank)}(?!\w)", c_low):
            roles.add(rank.capitalize())

    # 3. Các chức vụ Lãnh đạo cấp cao Đảng & Nhà nước
    if "tổng bí thư" in c_low:
        prefix = "Nguyên " if ("nguyên tổng bí thư" in c_low or "cựu tổng bí thư" in c_low) else ""
        roles.add(f"{prefix}Tổng Bí thư")
        organizations.add("Ban Chấp hành Trung ương Đảng")
        ban_nganh.add("Khối Đảng Trung ương")

    if "chủ tịch nước" in c_low:
        if "phó chủ tịch nước" in c_low:
            prefix = "Nguyên " if ("nguyên phó chủ tịch nước" in c_low or "cựu phó chủ tịch nước" in c_low) else ""
            roles.add(f"{prefix}Phó Chủ tịch nước")
        elif "văn phòng chủ tịch nước" not in c_low:
            prefix = "Nguyên " if ("nguyên chủ tịch nước" in c_low or "cựu chủ tịch nước" in c_low) else ""
            roles.add(f"{prefix}Chủ tịch nước")
            organizations.add("Nhà nước CHXHCN Việt Nam")

    if "thủ tướng" in c_low:
        if "phó thủ tướng thường trực" in c_low:
            roles.add("Phó Thủ tướng Thường trực Chính phủ")
            organizations.add("Chính phủ")
            ban_nganh.add("Khối Chính phủ")
        elif "phó thủ tướng" in c_low:
            prefix = "Nguyên " if ("nguyên phó thủ tướng" in c_low or "cựu phó thủ tướng" in c_low) else ""
            roles.add(f"{prefix}Phó Thủ tướng Chính phủ")
            organizations.add("Chính phủ")
            ban_nganh.add("Khối Chính phủ")
        else:
            prefix = "Nguyên " if ("nguyên thủ tướng" in c_low or "cựu thủ tướng" in c_low) else ""
            roles.add(f"{prefix}Thủ tướng Chính phủ")
            organizations.add("Chính phủ")
            ban_nganh.add("Khối Chính phủ")

    if "chủ tịch quốc hội" in c_low:
        if "phó chủ tịch thường trực quốc hội" in c_low:
            roles.add("Phó Chủ tịch Thường trực Quốc hội")
        elif "phó chủ tịch quốc hội" in c_low:
            prefix = "Nguyên " if "nguyên phó chủ tịch quốc hội" in c_low else ""
            roles.add(f"{prefix}Phó Chủ tịch Quốc hội")
        else:
            prefix = "Nguyên " if "nguyên chủ tịch quốc hội" in c_low else ""
            roles.add(f"{prefix}Chủ tịch Quốc hội")
        organizations.add("Quốc hội")
        ban_nganh.add("Khối Quốc hội")

    if "thường trực ban bí thư" in c_low:
        roles.add("Thường trực Ban Bí thư")
        organizations.add("Ban Bí thư Trung ương Đảng")
        ban_nganh.add("Khối Đảng Trung ương")

    if "ủy viên bộ chính trị" in c_low or "ủy viên thường vụ bộ chính trị" in c_low:
        prefix = "Nguyên " if "nguyên ủy viên bộ chính trị" in c_low else ""
        roles.add(f"{prefix}Ủy viên Bộ Chính trị")
        organizations.add("Bộ Chính trị")
        ban_nganh.add("Khối Đảng Trung ương")

    if "bí thư trung ương đảng" in c_low or "bí thư tw đảng" in c_low:
        prefix = "Nguyên " if "nguyên bí thư trung ương đảng" in c_low else ""
        roles.add(f"{prefix}Bí thư Trung ương Đảng")
        organizations.add("Ban Bí thư Trung ương Đảng")
        ban_nganh.add("Khối Đảng Trung ương")

    if any(k in c_low for k in ["ủy viên dự khuyết trung ương đảng", "ủy viên dự khuyết bch trung ương đảng", "ủy viên dự khuyết ban chấp hành trung ương đảng"]):
        roles.add("Ủy viên dự khuyết Trung ương Đảng")
        organizations.add("Ban Chấp hành Trung ương Đảng")
    elif any(k in c_low for k in ["ủy viên trung ương đảng", "ủy viên bch trung ương đảng", "ủy viên ban chấp hành trung ương đảng", "ủy viên tw đảng"]):
        prefix = "Nguyên " if "nguyên ủy viên" in c_low else ""
        roles.add(f"{prefix}Ủy viên Trung ương Đảng")
        organizations.add("Ban Chấp hành Trung ương Đảng")

    if "ủy viên thường vụ quân ủy trung ương" in c_low:
        roles.add("Ủy viên Thường vụ Quân ủy Trung ương")
        organizations.add("Quân ủy Trung ương")
        ban_nganh.add("Ngành Quốc phòng")
    elif "ủy viên quân ủy trung ương" in c_low:
        roles.add("Ủy viên Quân ủy Trung ương")
        organizations.add("Quân ủy Trung ương")
        ban_nganh.add("Ngành Quốc phòng")
    elif "phó bí thư quân ủy trung ương" in c_low:
        roles.add("Phó Bí thư Quân ủy Trung ương")
        organizations.add("Quân ủy Trung ương")
        ban_nganh.add("Ngành Quốc phòng")

    if "ủy viên ban thường vụ đảng ủy công an trung ương" in c_low or "ủy viên thường vụ đảng ủy công an trung ương" in c_low:
        roles.add("Ủy viên Ban Thường vụ Đảng ủy Công an Trung ương")
        organizations.add("Đảng ủy Công an Trung ương")
        ban_nganh.add("Ngành Công an")
    elif "bí thư đảng ủy công an trung ương" in c_low:
        roles.add("Bí thư Đảng ủy Công an Trung ương")
        organizations.add("Đảng ủy Công an Trung ương")
        ban_nganh.add("Ngành Công an")

    if "ủy ban thường vụ quốc hội" in c_low:
        if "ủy viên" in c_low:
            roles.add("Ủy viên Ủy ban Thường vụ Quốc hội")
        organizations.add("Ủy ban Thường vụ Quốc hội")
        ban_nganh.add("Khối Quốc hội")

    if "tổng thư ký quốc hội" in c_low:
        roles.add("Tổng Thư ký Quốc hội")
        organizations.add("Quốc hội")
        ban_nganh.add("Văn phòng Quốc hội")

    # 4. Kiểm tra các Ban Đảng Trung ương
    for key, (dept_name, org_name) in CENTRAL_PARTY_DEPTS.items():
        if key in c_low:
            ban_nganh.add(dept_name)
            organizations.add(org_name)
            if dept_name != org_name and dept_name.startswith(("Ban ", "Ủy ban ", "Văn phòng ", "Học viện ")):
                organizations.add(dept_name)
            if "phó trưởng ban thường trực" in c_low:
                roles.add("Phó Trưởng ban Thường trực")
            elif "phó trưởng ban" in c_low or "phó trưởng" in c_low:
                roles.add("Phó Trưởng ban")
            elif "trưởng ban" in c_low or "trưởng" in c_low:
                roles.add("Trưởng ban")
            elif "phó chủ nhiệm thường trực" in c_low:
                roles.add("Phó Chủ nhiệm Thường trực")
            elif "phó chủ nhiệm" in c_low:
                roles.add("Phó Chủ nhiệm")
            elif "chủ nhiệm" in c_low:
                roles.add("Chủ nhiệm")
            elif "phó chánh văn phòng thường trực" in c_low:
                roles.add("Phó Chánh Văn phòng Thường trực")
            elif "phó chánh văn phòng" in c_low:
                roles.add("Phó Chánh Văn phòng")
            elif "chánh văn phòng" in c_low:
                roles.add("Chánh Văn phòng")
            elif "phó giám đốc" in c_low:
                roles.add("Phó Giám đốc")
            elif "giám đốc" in c_low:
                roles.add("Giám đốc")
            elif "phó bí thư thường trực" in c_low:
                roles.add("Phó Bí thư Thường trực Đảng ủy")
            elif "phó bí thư" in c_low:
                roles.add("Phó Bí thư Đảng ủy")
            elif "bí thư" in c_low:
                roles.add("Bí thư Đảng ủy")
            elif "ủy viên" in c_low:
                roles.add(f"Ủy viên {dept_name}")

    # Xử lý trường hợp viết tắt chữ "Ban" khi nối với Trưởng ban (VD: "Trưởng ban Tổ chức Trung ương", "Phó Trưởng ban Tuyên giáo Trung ương")
    short_central_depts = [
        ("tổ chức trung ương", "Ban Tổ chức Trung ương"),
        ("tuyên giáo và dân vận trung ương", "Ban Tuyên giáo và Dân vận Trung ương"),
        ("tuyên giáo trung ương", "Ban Tuyên giáo Trung ương"),
        ("dân vận trung ương", "Ban Dân vận Trung ương"),
        ("nội chính trung ương", "Ban Nội chính Trung ương"),
        ("chính sách, chiến lược trung ương", "Ban Chính sách, chiến lược Trung ương"),
        ("kinh tế trung ương", "Ban Kinh tế Trung ương"),
        ("đối ngoại trung ương", "Ban Đối ngoại Trung ương"),
    ]
    for short_k, full_dept in short_central_depts:
        if short_k in c_low:
            ban_nganh.add(full_dept)
            organizations.add(full_dept)
            organizations.add("Ban Chấp hành Trung ương Đảng")
            if "phó trưởng ban thường trực" in c_low or "phó trưởng thường trực" in c_low:
                roles.add("Phó Trưởng ban Thường trực")
            elif "phó trưởng" in c_low:
                roles.add("Phó Trưởng ban")
            elif "trưởng" in c_low:
                roles.add("Trưởng ban")

    # 5. Kiểm tra các Ủy ban của Quốc hội & Văn phòng QH / CTN
    for key, comm_name in NATIONAL_ASSEMBLY_COMMITTEES.items():
        if key in c_low:
            ban_nganh.add(comm_name)
            organizations.add("Quốc hội" if "chủ tịch nước" not in key else "Văn phòng Chủ tịch nước")
            organizations.add(comm_name)
            if "phó chủ nhiệm thường trực" in c_low:
                roles.add("Phó Chủ nhiệm Thường trực Ủy ban của Quốc hội" if "ủy ban" in key else "Phó Chủ nhiệm Thường trực")
            elif "phó chủ nhiệm" in c_low:
                roles.add("Phó Chủ nhiệm Ủy ban của Quốc hội" if "ủy ban" in key else "Phó Chủ nhiệm")
            elif "chủ nhiệm" in c_low:
                roles.add("Chủ nhiệm Ủy ban của Quốc hội" if "ủy ban" in key else "Chủ nhiệm")
            elif "phó chủ tịch" in c_low and "hội đồng dân tộc" in key:
                roles.add("Phó Chủ tịch Hội đồng Dân tộc")
            elif "chủ tịch" in c_low and "hội đồng dân tộc" in key:
                roles.add("Chủ tịch Hội đồng Dân tộc")
            elif "phó trưởng ban" in c_low:
                roles.add("Phó Trưởng ban")
            elif "trưởng ban" in c_low:
                roles.add("Trưởng ban")
            elif "ủy viên thường trực" in c_low:
                roles.add("Ủy viên Thường trực Ủy ban của Quốc hội")
            elif "ủy viên chuyên trách" in c_low:
                roles.add("Ủy viên chuyên trách Ủy ban của Quốc hội")
            elif "ủy viên" in c_low:
                roles.add("Ủy viên Ủy ban của Quốc hội")

    # 6. Kiểm tra 14 Bộ, các Bộ cũ & Cơ quan ngang Bộ
    matched_ministry = False
    for key, (min_name, sector_name) in sorted(MINISTRY_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if key in c_low:
            organizations.add(min_name)
            ban_nganh.add(sector_name)
            matched_ministry = True
            break

    # Trường hợp viết tắt chữ "Bộ" sau "Bộ trưởng" / "Thứ trưởng" (VD: "Bộ trưởng Công an", "Bộ trưởng Quốc phòng", "Bộ trưởng Ngoại giao")
    if not matched_ministry and ("bộ trưởng" in c_low or "thứ trưởng" in c_low):
        short_ministries = {
            "quốc phòng": ("Bộ Quốc phòng", "Ngành Quốc phòng"),
            "công an": ("Bộ Công an", "Ngành Công an"),
            "ngoại giao": ("Bộ Ngoại giao", "Ngành Ngoại giao"),
            "nội vụ": ("Bộ Nội vụ", "Ngành Nội vụ"),
            "tư pháp": ("Bộ Tư pháp", "Ngành Tư pháp"),
            "tài chính": ("Bộ Tài chính", "Ngành Tài chính"),
            "công thương": ("Bộ Công Thương", "Ngành Công Thương"),
            "nông nghiệp và môi trường": ("Bộ Nông nghiệp và Môi trường", "Ngành Nông nghiệp và Môi trường"),
            "xây dựng": ("Bộ Xây dựng", "Ngành Xây dựng"),
            "văn hóa, thể thao và du lịch": ("Bộ Văn hóa, Thể thao và Du lịch", "Ngành Văn hóa, Thể thao và Du lịch"),
            "khoa học và công nghệ": ("Bộ Khoa học và Công nghệ", "Ngành Khoa học và Công nghệ"),
            "giáo dục và đào tạo": ("Bộ Giáo dục và Đào tạo", "Ngành Giáo dục và Đào tạo"),
            "y tế": ("Bộ Y tế", "Ngành Y tế"),
            "dân tộc và tôn giáo": ("Bộ Dân tộc và Tôn giáo", "Ngành Dân tộc và Tôn giáo"),
            "kế hoạch và đầu tư": ("Bộ Kế hoạch và Đầu tư", "Ngành Kế hoạch và Đầu tư"),
            "giao thông vận tải": ("Bộ Giao thông vận tải", "Ngành Giao thông vận tải"),
            "tài nguyên và môi trường": ("Bộ Tài nguyên và Môi trường", "Ngành Tài nguyên và Môi trường"),
            "thông tin và truyền thông": ("Bộ Thông tin và Truyền thông", "Ngành Thông tin và Truyền thông"),
            "lao động - thương binh và xã hội": ("Bộ Lao động - Thương binh và Xã hội", "Ngành Lao động - Thương binh và Xã hội"),
        }
        for sk, (min_name, sector_name) in short_ministries.items():
            if sk in c_low:
                organizations.add(min_name)
                ban_nganh.add(sector_name)
                break

    if "thứ trưởng thường trực" in c_low:
        roles.add("Thứ trưởng Thường trực")
    elif "thứ trưởng" in c_low:
        prefix = "Nguyên " if ("nguyên thứ trưởng" in c_low or "cựu thứ trưởng" in c_low) else ""
        roles.add(f"{prefix}Thứ trưởng")
    elif "bộ trưởng" in c_low and "trợ lý bộ trưởng" not in c_low:
        prefix = "Nguyên " if ("nguyên bộ trưởng" in c_low or "cựu bộ trưởng" in c_low) else ("Quyền " if "quyền bộ trưởng" in c_low else "")
        roles.add(f"{prefix}Bộ trưởng")

    if "thống đốc" in c_low:
        if "phó thống đốc" in c_low:
            roles.add("Phó Thống đốc Ngân hàng Nhà nước")
        else:
            roles.add("Thống đốc Ngân hàng Nhà nước")
        organizations.add("Ngân hàng Nhà nước Việt Nam")
        ban_nganh.add("Ngành Ngân hàng")

    if "tổng thanh tra" in c_low:
        if "phó tổng thanh tra" in c_low:
            roles.add("Phó Tổng Thanh tra Chính phủ")
        else:
            roles.add("Tổng Thanh tra Chính phủ")
        organizations.add("Thanh tra Chính phủ")
        ban_nganh.add("Ngành Thanh tra")

    if "tổng kiểm toán" in c_low:
        if "phó tổng kiểm toán" in c_low:
            roles.add("Phó Tổng Kiểm toán Nhà nước")
        else:
            roles.add("Tổng Kiểm toán Nhà nước")
        organizations.add("Kiểm toán Nhà nước")
        ban_nganh.add("Ngành Kiểm toán")

    # 7. Mặt trận Tổ quốc & các đoàn thể chính trị - xã hội
    if any(k in c_low for k in ["mặt trận tổ quốc", "mttq", "ủy ban mặt trận"]):
        is_central = "trung ương" in c_low or ("tỉnh" not in c_low and "thành phố" not in c_low and "tp" not in c_low and "xã" not in c_low and "phường" not in c_low and not active_prov)
        if is_central:
            org_mttq = "Ủy ban Trung ương MTTQ Việt Nam"
        elif active_prov:
            unit = "thành phố" if active_prov in {"Hà Nội", "TP.HCM", "Hải Phòng", "Đà Nẵng", "Huế", "Cần Thơ"} else "tỉnh"
            org_mttq = f"Ủy ban MTTQ Việt Nam {unit} {active_prov}"
        else:
            org_mttq = "Ủy ban MTTQ Việt Nam địa phương"
        organizations.add(org_mttq)
        ban_nganh.add("Khối Mặt trận - Đoàn thể")
        if "phó chủ tịch thường trực" in c_low:
            roles.add("Phó Chủ tịch Thường trực Ủy ban MTTQ")
        elif "phó chủ tịch" in c_low:
            roles.add("Phó Chủ tịch Ủy ban MTTQ")
        elif "chủ tịch" in c_low:
            roles.add("Chủ tịch Ủy ban MTTQ")

    mass_orgs = [
        ("tổng liên đoàn lao động việt nam", "Tổng Liên đoàn Lao động Việt Nam"),
        ("liên đoàn lao động", f"Liên đoàn Lao động {active_prov}".strip()),
        ("trung ương đoàn", "Trung ương Đoàn TNCS Hồ Chí Minh"),
        ("thành đoàn", f"Thành đoàn {active_prov}".strip()),
        ("tỉnh đoàn", f"Tỉnh đoàn {active_prov}".strip()),
        ("hội liên hiệp phụ nữ", "Hội Liên hiệp Phụ nữ"),
        ("hội nông dân", "Hội Nông dân"),
        ("hội cựu chiến binh", "Hội Cựu chiến binh"),
        ("hội sinh viên", "Hội Sinh viên Việt Nam"),
    ]
    for mk, m_org in mass_orgs:
        if mk in c_low:
            organizations.add(m_org)
            ban_nganh.add("Khối Mặt trận - Đoàn thể")
            if "phó chủ tịch" in c_low:
                roles.add("Phó Chủ tịch")
            elif "chủ tịch" in c_low:
                roles.add("Chủ tịch")
            elif "bí thư thứ nhất" in c_low:
                roles.add("Bí thư thứ nhất Trung ương Đoàn")
            elif "phó bí thư" in c_low:
                roles.add("Phó Bí thư Đoàn")
            elif "bí thư" in c_low:
                roles.add("Bí thư Đoàn")

    # 8. Cấp Tỉnh ủy / Thành ủy / Đảng ủy địa phương & Các Ban Đảng địa phương
    for party_organ, canon_organ in [("thành ủy", "Thành ủy"), ("tỉnh ủy", "Tỉnh ủy"), ("huyện ủy", "Huyện ủy"), ("quận ủy", "Quận ủy"), ("thị ủy", "Thị ủy")]:
        if party_organ in c_low:
            full_organ = f"{canon_organ} {active_prov}".strip() if (active_prov and party_organ in ("thành ủy", "tỉnh ủy")) else canon_organ
            organizations.add(full_organ)
            # Kiểm tra các Ban thuộc Tỉnh ủy / Thành ủy
            local_party_depts = [
                ("ban tổ chức", f"Ban Tổ chức {full_organ}"),
                ("ban nội chính", f"Ban Nội chính {full_organ}"),
                ("ban tuyên giáo và dân vận", f"Ban Tuyên giáo và Dân vận {full_organ}"),
                ("ban tuyên giáo", f"Ban Tuyên giáo {full_organ}"),
                ("ban dân vận", f"Ban Dân vận {full_organ}"),
                ("ủy ban kiểm tra", f"Ủy ban Kiểm tra {full_organ}"),
                ("văn phòng", f"Văn phòng {full_organ}"),
            ]
            matched_local_dept = False
            for ldk, ld_full in local_party_depts:
                if ldk in c_low:
                    ban_nganh.add(ld_full)
                    organizations.add(ld_full)
                    matched_local_dept = True
                    if "phó trưởng ban thường trực" in c_low:
                        roles.add("Phó Trưởng ban Thường trực")
                    elif "phó trưởng ban" in c_low or "phó trưởng" in c_low:
                        roles.add("Phó Trưởng ban")
                    elif "trưởng ban" in c_low or "trưởng" in c_low:
                        roles.add("Trưởng ban")
                    elif "phó chủ nhiệm thường trực" in c_low:
                        roles.add("Phó Chủ nhiệm Thường trực Ủy ban Kiểm tra")
                    elif "phó chủ nhiệm" in c_low:
                        roles.add("Phó Chủ nhiệm Ủy ban Kiểm tra")
                    elif "chủ nhiệm" in c_low:
                        roles.add("Chủ nhiệm Ủy ban Kiểm tra")
                    elif "phó chánh văn phòng" in c_low:
                        roles.add("Phó Chánh Văn phòng")
                    elif "chánh văn phòng" in c_low:
                        roles.add("Chánh Văn phòng")
                    elif "ủy viên" in c_low and "ủy ban kiểm tra" in ldk:
                        roles.add(f"Ủy viên Ủy ban Kiểm tra {canon_organ}")
                    break

            if not matched_local_dept:
                ban_nganh.add(f"Khối Đảng {canon_organ}")
                if f"phó bí thư thường trực {party_organ}" in c_low or ("phó bí thư thường trực" in c_low):
                    roles.add(f"Phó Bí thư Thường trực {canon_organ}")
                elif f"phó bí thư {party_organ}" in c_low or "phó bí thư" in c_low:
                    roles.add(f"Phó Bí thư {canon_organ}")
                elif f"bí thư {party_organ}" in c_low or "bí thư" in c_low:
                    prefix = "Nguyên " if "nguyên bí thư" in c_low else ""
                    roles.add(f"{prefix}Bí thư {canon_organ}")
                elif "ủy viên ban thường vụ" in c_low or "ủy viên thường vụ" in c_low:
                    roles.add(f"Ủy viên Ban Thường vụ {canon_organ}")
                elif "ủy viên ban chấp hành" in c_low or f"{party_organ} viên" in c_low:
                    roles.add(f"{canon_organ} viên")

    # Đảng ủy (xã, phường, các cơ quan, quân khu, bộ...)
    if "đảng ủy" in c_low or "đảng bộ" in c_low:
        m_du = re.search(
            r"(Đảng\s+(?:ủy|bộ)\s+(?:các\s+cơ\s+quan\s+Đảng\s+[^\.,;:\n\(\)]+|UBND\s+[^\.,;:\n\(\)]+|"
            r"(?:xã|phường|thị\s+trấn|đặc\s+khu)\s+[A-ZÀ-ỸĐ][a-zà-ỹđ]+(?:\s+[A-ZÀ-ỸĐ][a-zà-ỹđ]+){0,2}|"
            r"Quân\s+khu\s+\d+|Bộ\s+[^\.,;:\n\(\)]+|Công\s+an\s+[^\.,;:\n\(\)]+))",
            c_clean, re.IGNORECASE
        )
        if m_du:
            du_org = m_du.group(1).strip()
            organizations.add(du_org)
        elif "ban thường vụ đảng ủy" in c_low:
            organizations.add("Ban Thường vụ Đảng ủy")
        else:
            organizations.add("Đảng ủy")

        if "trưởng ban xây dựng đảng" in c_low:
            roles.add("Trưởng ban Xây dựng Đảng")
            ban_nganh.add("Ban Xây dựng Đảng")
        elif "phó bí thư thường trực đảng ủy" in c_low or ("phó bí thư thường trực" in c_low and "tỉnh ủy" not in c_low and "thành ủy" not in c_low):
            roles.add("Phó Bí thư Thường trực Đảng ủy")
        elif "phó bí thư đảng ủy" in c_low or ("phó bí thư" in c_low and "tỉnh ủy" not in c_low and "thành ủy" not in c_low):
            roles.add("Phó Bí thư Đảng ủy")
        elif "bí thư đảng ủy" in c_low or ("bí thư" in c_low and "tỉnh ủy" not in c_low and "thành ủy" not in c_low and "trung ương" not in c_low and "chi bộ" not in c_low):
            roles.add("Bí thư Đảng ủy")
        elif "ủy viên ban thường vụ đảng ủy" in c_low:
            roles.add("Ủy viên Ban Thường vụ Đảng ủy")
        elif "đảng ủy viên" in c_low:
            roles.add("Đảng ủy viên")

    if "bí thư chi bộ" in c_low:
        roles.add("Bí thư Chi bộ")

    # 9. UBND & HĐND các cấp (Tỉnh, Thành phố, Quận, Huyện, Thị xã, Phường, Xã)
    if any(k in c_low for k in ["ubnd", "ủy ban nhân dân"]):
        # Kiểm tra cấp xã/phường/huyện/quận
        m_local_ub = re.search(
            r"(?:UBND|Ủy\s+ban\s+nhân\s+dân)\s+((?:xã|phường|thị\s+trấn|huyện|quận|thị\s+xã|đặc\s+khu)\s+[A-ZÀ-ỸĐ][a-zà-ỹđ]+(?:\s+[A-ZÀ-ỸĐ][a-zà-ỹđ]+){0,2})",
            c_clean, re.IGNORECASE
        )
        if m_local_ub:
            sub_unit = m_local_ub.group(1).strip()
            unit_type = sub_unit.split()[0].lower()
            organizations.add(f"UBND {sub_unit}")
            ban_nganh.add("Chính quyền địa phương")
            if "phó chủ tịch thường trực" in c_low:
                roles.add(f"Phó Chủ tịch Thường trực UBND {unit_type}")
            elif "phó chủ tịch" in c_low:
                roles.add(f"Phó Chủ tịch UBND {unit_type}")
            elif "chủ tịch" in c_low:
                roles.add(f"Chủ tịch UBND {unit_type}")
        else:
            is_city = "thành phố" in c_low or "tp" in c_low or (active_prov in {"Hà Nội", "TP.HCM", "Hải Phòng", "Đà Nẵng", "Huế", "Cần Thơ"})
            unit_label = "thành phố" if is_city else "tỉnh"
            org_ub = f"UBND {unit_label} {active_prov}".strip() if active_prov else f"UBND {unit_label}"
            organizations.add(org_ub)
            ban_nganh.add("Khối Chính quyền địa phương")
            if "chánh văn phòng" in c_low:
                roles.add("Phó Chánh Văn phòng UBND" if "phó chánh" in c_low else "Chánh Văn phòng UBND")
                ban_nganh.add(f"Văn phòng {org_ub}")
            elif "phó chủ tịch thường trực" in c_low:
                roles.add(f"Phó Chủ tịch Thường trực UBND {unit_label}")
            elif "phó chủ tịch" in c_low:
                prefix = "Nguyên " if ("nguyên phó chủ tịch" in c_low or "cựu phó chủ tịch" in c_low) else ""
                roles.add(f"{prefix}Phó Chủ tịch UBND {unit_label}")
            elif "chủ tịch" in c_low:
                prefix = "Nguyên " if ("nguyên chủ tịch" in c_low or "cựu chủ tịch" in c_low) else ("Quyền " if "quyền chủ tịch" in c_low else "")
                roles.add(f"{prefix}Chủ tịch UBND {unit_label}")

    if any(k in c_low for k in ["hđnd", "hội đồng nhân dân"]):
        m_local_hd = re.search(
            r"(?:HĐND|Hội\s+đồng\s+nhân\s+dân)\s+((?:xã|phường|thị\s+trấn|huyện|quận|thị\s+xã|đặc\s+khu)\s+[A-ZÀ-ỸĐ][a-zà-ỹđ]+(?:\s+[A-ZÀ-ỸĐ][a-zà-ỹđ]+){0,2})",
            c_clean, re.IGNORECASE
        )
        if m_local_hd:
            sub_unit = m_local_hd.group(1).strip()
            unit_type = sub_unit.split()[0].lower()
            organizations.add(f"HĐND {sub_unit}")
            ban_nganh.add("Hội đồng nhân dân địa phương")
            if "phó chủ tịch" in c_low:
                roles.add(f"Phó Chủ tịch HĐND {unit_type}")
            elif "chủ tịch" in c_low:
                roles.add(f"Chủ tịch HĐND {unit_type}")
        else:
            is_city = "thành phố" in c_low or "tp" in c_low or (active_prov in {"Hà Nội", "TP.HCM", "Hải Phòng", "Đà Nẵng", "Huế", "Cần Thơ"})
            unit_label = "thành phố" if is_city else "tỉnh"
            org_hd = f"HĐND {unit_label} {active_prov}".strip() if active_prov else f"HĐND {unit_label}"
            organizations.add(org_hd)
            ban_nganh.add("Khối HĐND địa phương")
            for ban_hd in ["Ban Pháp chế", "Ban Kinh tế - Ngân sách", "Ban Văn hóa - Xã hội", "Ban Đô thị", "Ban Dân tộc"]:
                if ban_hd.lower() in c_low:
                    ban_nganh.add(f"{ban_hd} {org_hd}")
                    roles.add("Phó Trưởng ban HĐND" if "phó trưởng" in c_low else "Trưởng ban HĐND")
            if "chánh văn phòng" in c_low:
                roles.add("Phó Chánh Văn phòng Đoàn ĐBQH và HĐND" if "phó chánh" in c_low else "Chánh Văn phòng Đoàn ĐBQH và HĐND")
                ban_nganh.add(f"Văn phòng Đoàn ĐBQH và {org_hd}")
            elif "phó chủ tịch thường trực" in c_low:
                roles.add(f"Phó Chủ tịch Thường trực HĐND {unit_label}")
            elif "phó chủ tịch" in c_low:
                roles.add(f"Phó Chủ tịch HĐND {unit_label}")
            elif "chủ tịch" in c_low:
                roles.add(f"Chủ tịch HĐND {unit_label}")

    # 10. Các Sở chuyên môn thuộc tỉnh / thành phố
    for dept in PROVINCIAL_DEPT_NAMES:
        if dept.lower() in c_low:
            full_dept = f"{dept} {active_prov}".strip() if active_prov else dept
            ban_nganh.add(dept)
            organizations.add(full_dept)
            if "phó giám đốc" in c_low:
                roles.add("Phó Giám đốc Sở")
            elif "giám đốc" in c_low:
                roles.add("Giám đốc Sở")
            elif "chánh thanh tra" in c_low:
                roles.add("Chánh Thanh tra Sở")
            elif "chánh văn phòng" in c_low:
                roles.add("Chánh Văn phòng Sở")
            break
    else:
        # Trường hợp "Sở ..." khác hoặc viết tắt
        m_so = re.search(r"\b(Sở\s+[A-ZÀ-ỸĐ][^\.,;:\n\(\)]{2,35})", c_clean)
        if m_so:
            so_name = m_so.group(1).strip()
            ban_nganh.add(so_name)
            organizations.add(f"{so_name} {active_prov}".strip() if active_prov and active_prov not in so_name else so_name)
            if "phó giám đốc" in c_low:
                roles.add("Phó Giám đốc Sở")
            elif "giám đốc" in c_low:
                roles.add("Giám đốc Sở")

    # 11. Cục / Tổng cục / Chi cục / Vụ / Viện / Văn phòng / Ban Chỉ đạo / Ban Quản lý / Ban Cơ yếu
    if "ban cơ yếu chính phủ" in c_low:
        ban_nganh.add("Ban Cơ yếu Chính phủ")
        organizations.add("Ban Cơ yếu Chính phủ")
        roles.add("Phó Trưởng ban Cơ yếu Chính phủ" if "phó trưởng" in c_low else "Trưởng ban Cơ yếu Chính phủ")

    if "ủy ban nhà nước về người việt nam ở nước ngoài" in c_low:
        ban_nganh.add("Ủy ban Nhà nước về người Việt Nam ở nước ngoài")
        organizations.add("Bộ Ngoại giao")
        organizations.add("Ủy ban Nhà nước về người Việt Nam ở nước ngoài")
        roles.add("Phó Chủ nhiệm Ủy ban" if "phó chủ nhiệm" in c_low else "Chủ nhiệm Ủy ban")

    if "ủy ban cạnh tranh quốc gia" in c_low:
        ban_nganh.add("Ủy ban Cạnh tranh Quốc gia")
        organizations.add("Bộ Công Thương")
        organizations.add("Ủy ban Cạnh tranh Quốc gia")
        roles.add("Phó Chủ tịch Ủy ban" if "phó chủ tịch" in c_low else "Chủ tịch Ủy ban")

    # Bắt Tổng cục / Cục / Chi cục / Vụ
    m_cuc = re.search(
        r"\b((?:Tổng\s+cục|Chi\s+cục|Cục|Vụ)\s+[A-ZÀ-ỸĐa-zà-ỹđ][^\.,;:\n\(\)]{2,60})",
        c_clean
    )
    if m_cuc:
        cuc_name = m_cuc.group(1).strip()
        ban_nganh.add(cuc_name)
        organizations.add(cuc_name)
    elif any(k in c_low for k in ["tổng cục trưởng", "phó tổng cục trưởng", "chi cục trưởng", "phó chi cục trưởng", "cục trưởng", "phó cục trưởng", "vụ trưởng", "phó vụ trưởng"]):
        # Trường hợp lược bỏ chữ Cục/Vụ (VD: "Phó Cục trưởng Đầu tư nước ngoài")
        m_short_cuc = re.search(
            r"(?:Tổng\s+cục\s+trưởng|Chi\s+cục\s+trưởng|Cục\s+trưởng|Vụ\s+trưởng)\s+([A-ZÀ-ỸĐ][^\.,;:\n\(\)]{2,45})",
            c_clean, re.IGNORECASE
        )
        if m_short_cuc:
            prefix_type = "Cục" if "cục trưởng" in c_low else "Vụ"
            cuc_name = f"{prefix_type} {m_short_cuc.group(1).strip()}"
            ban_nganh.add(cuc_name)
            organizations.add(cuc_name)

    if "phó tổng cục trưởng" in c_low:
        roles.add("Phó Tổng Cục trưởng")
    elif "tổng cục trưởng" in c_low:
        roles.add("Tổng Cục trưởng")
    elif "phó chi cục trưởng" in c_low:
        roles.add("Phó Chi cục trưởng")
    elif "chi cục trưởng" in c_low:
        roles.add("Chi cục trưởng")
    elif "phó cục trưởng" in c_low:
        roles.add("Phó Cục trưởng")
    elif "cục trưởng" in c_low:
        roles.add("Cục trưởng")
    elif "phó vụ trưởng" in c_low:
        roles.add("Phó Vụ trưởng")
    elif "vụ trưởng" in c_low:
        roles.add("Vụ trưởng")

    # Bắt Ban Chỉ đạo / Ban Quản lý
    m_bcd = re.search(r"\b(Ban\s+(?:Chỉ\s+đạo|Quản\s+lý)\s+[^\.,;:\n\(\)]{3,85})", c_clean, re.IGNORECASE)
    if m_bcd:
        bcd_name = m_bcd.group(1).strip()
        ban_nganh.add(bcd_name)
        organizations.add(bcd_name)
        if "phó trưởng ban thường trực" in c_low:
            roles.add("Phó Trưởng ban Thường trực Ban Chỉ đạo" if "chỉ đạo" in c_low else "Phó Trưởng ban Quản lý")
        elif "phó trưởng ban" in c_low or "phó trưởng" in c_low:
            roles.add("Phó Trưởng ban Chỉ đạo" if "chỉ đạo" in c_low else "Phó Trưởng ban Quản lý")
        elif "trưởng ban" in c_low or "trưởng" in c_low:
            roles.add("Trưởng ban Chỉ đạo" if "chỉ đạo" in c_low else "Trưởng ban Quản lý")

    # 12. Quân khu, Quân chủng, Binh chủng, Bộ Tư lệnh, Bộ đội Biên phòng, Công an địa phương
    m_qk = re.search(r"\b(Quân\s+khu\s+\d+|Quân\s+chủng\s+[A-ZÀ-ỸĐ][^\.,;:\n\(\)]{2,30}|Binh\s+chủng\s+[A-ZÀ-ỸĐ][^\.,;:\n\(\)]{2,30}|Quân\s+đoàn\s+\d+)", c_clean, re.IGNORECASE)
    if m_qk:
        qk_name = m_qk.group(1).strip()
        organizations.add(qk_name)
        ban_nganh.add("Ngành Quốc phòng")
    elif "quân khu" in c_low:
        organizations.add("Quân khu")
        ban_nganh.add("Ngành Quốc phòng")

    if "bộ đội biên phòng" in c_low or "biên phòng" in c_low:
        bp_org = f"Bộ đội Biên phòng tỉnh {active_prov}" if active_prov else "Bộ đội Biên phòng"
        organizations.add(bp_org)
        ban_nganh.add("Ngành Quốc phòng - Biên phòng")

    if "công an tỉnh" in c_low or "công an thành phố" in c_low or "công an tp" in c_low or (active_prov and f"công an {active_prov.lower()}" in c_low):
        is_city = "thành phố" in c_low or "tp" in c_low or (active_prov in {"Hà Nội", "TP.HCM", "Hải Phòng", "Đà Nẵng", "Huế", "Cần Thơ"})
        unit_label = "TP" if is_city else "tỉnh"
        ca_org = f"Công an {unit_label} {active_prov}".strip() if active_prov else f"Công an {unit_label}"
        organizations.add(ca_org)
        ban_nganh.add("Ngành Công an")
        if "phó giám đốc" in c_low:
            roles.add(f"Phó Giám đốc Công an {unit_label}")
        elif "giám đốc" in c_low:
            roles.add(f"Giám đốc Công an {unit_label}")

    if "phó tổng tham mưu trưởng" in c_low:
        roles.add("Phó Tổng Tham mưu trưởng QĐND Việt Nam")
        organizations.add("Bộ Tổng Tham mưu QĐND Việt Nam")
        organizations.add("Bộ Quốc phòng")
        ban_nganh.add("Ngành Quốc phòng")
    elif "tổng tham mưu trưởng" in c_low:
        roles.add("Tổng Tham mưu trưởng QĐND Việt Nam")
        organizations.add("Bộ Tổng Tham mưu QĐND Việt Nam")
        organizations.add("Bộ Quốc phòng")
        ban_nganh.add("Ngành Quốc phòng")
    elif "tham mưu trưởng" in c_low:
        roles.add("Tham mưu trưởng")
        ban_nganh.add("Ngành Quốc phòng")

    if "tổng cục chính trị" in c_low:
        organizations.add("Tổng cục Chính trị QĐND Việt Nam")
        organizations.add("Bộ Quốc phòng")
        ban_nganh.add("Tổng cục Chính trị QĐND Việt Nam")
        roles.add("Phó Chủ nhiệm Tổng cục Chính trị" if "phó chủ nhiệm" in c_low else "Chủ nhiệm Tổng cục Chính trị")
    elif "chủ nhiệm chính trị" in c_low:
        roles.add("Phó Chủ nhiệm Chính trị" if "phó chủ nhiệm" in c_low else "Chủ nhiệm Chính trị")
        ban_nganh.add("Ngành Quốc phòng")

    if "phó tư lệnh" in c_low:
        roles.add("Phó Tư lệnh")
        ban_nganh.add("Ngành Quốc phòng")
    elif "tư lệnh" in c_low and "bộ tư lệnh" not in c_low:
        roles.add("Tư lệnh")
        ban_nganh.add("Ngành Quốc phòng")

    if "phó chính ủy" in c_low:
        roles.add("Phó Chính ủy")
        ban_nganh.add("Ngành Quốc phòng")
    elif "chính ủy" in c_low:
        roles.add("Chính ủy")
        ban_nganh.add("Ngành Quốc phòng")

    if "chỉ huy trưởng" in c_low:
        roles.add("Phó Chỉ huy trưởng" if "phó chỉ huy" in c_low else "Chỉ huy trưởng")
        ban_nganh.add("Ngành Quốc phòng")

    # 13. Tòa án, Viện kiểm sát, Thanh tra địa phương & Đoàn ĐBQH
    if "chánh án" in c_low:
        roles.add("Phó Chánh án TAND" if "phó chánh án" in c_low else "Chánh án TAND")
        ban_nganh.add("Ngành Tòa án")
        if "tối cao" not in c_low:
            organizations.add(f"TAND tỉnh/TP {active_prov}".strip() if active_prov else "Tòa án nhân dân")

    if "viện kiểm sát" in c_low:
        roles.add("Phó Viện trưởng VKSND" if "phó viện trưởng" in c_low else "Viện trưởng VKSND")
        ban_nganh.add("Ngành Kiểm sát")
        if "tối cao" not in c_low:
            organizations.add(f"VKSND tỉnh/TP {active_prov}".strip() if active_prov else "Viện kiểm sát nhân dân")

    if "chánh thanh tra" in c_low:
        roles.add("Phó Chánh Thanh tra" if "phó chánh thanh tra" in c_low else "Chánh Thanh tra")
        ban_nganh.add("Ngành Thanh tra")

    if "đoàn đại biểu quốc hội" in c_low or "đoàn đbqh" in c_low or "đại biểu quốc hội" in c_low or "đbqh" in c_low:
        if "phó trưởng đoàn" in c_low:
            roles.add("Phó Trưởng đoàn ĐBQH")
        elif "trưởng đoàn" in c_low:
            roles.add("Trưởng đoàn ĐBQH")
        else:
            roles.add("Đại biểu Quốc hội")
        organizations.add(f"Đoàn ĐBQH {active_prov}".strip() if active_prov else "Quốc hội")
        ban_nganh.add("Khối Quốc hội")

    # 14. Fallback cho các chức vụ chung nếu chưa khớp cụ thể ở trên
    if not roles:
        generic_role_map = [
            ("phó chánh văn phòng thường trực", "Phó Chánh Văn phòng Thường trực"),
            ("phó chánh văn phòng", "Phó Chánh Văn phòng"),
            ("chánh văn phòng", "Chánh Văn phòng"),
            ("phó trưởng ban thường trực", "Phó Trưởng ban Thường trực"),
            ("phó trưởng ban", "Phó Trưởng ban"),
            ("trưởng ban", "Trưởng ban"),
            ("phó chủ nhiệm thường trực", "Phó Chủ nhiệm Thường trực"),
            ("phó chủ nhiệm", "Phó Chủ nhiệm"),
            ("chủ nhiệm", "Chủ nhiệm"),
            ("phó viện trưởng", "Phó Viện trưởng"),
            ("viện trưởng", "Viện trưởng"),
            ("phó giám đốc", "Phó Giám đốc"),
            ("giám đốc", "Giám đốc"),
            ("phó bí thư thường trực", "Phó Bí thư Thường trực"),
            ("phó bí thư", "Phó Bí thư"),
            ("bí thư", "Bí thư"),
            ("phó chủ tịch thường trực", "Phó Chủ tịch Thường trực"),
            ("phó chủ tịch", "Phó Chủ tịch"),
            ("chủ tịch", "Chủ tịch"),
            ("đại sứ", "Đại sứ"),
            ("thứ trưởng", "Thứ trưởng"),
            ("bộ trưởng", "Bộ trưởng"),
        ]
        for gk, g_val in generic_role_map:
            if gk in c_low:
                roles.add(g_val)
                break

    # Làm sạch tên cơ quan / ban ngành quá ngắn hoặc nhiễu
    clean_orgs = {o.strip(" ,.;:-–—") for o in organizations if len(o.strip(" ,.;:-–—")) >= 4}
    clean_depts = {d.strip(" ,.;:-–—") for d in ban_nganh if len(d.strip(" ,.;:-–—")) >= 4}

    return {
        "roles": roles,
        "ban_nganh": clean_depts,
        "organizations": clean_orgs,
        "provinces": provinces,
    }


# ============ 6. NHẬN DIỆN & BÓC TÁCH NHÂN VẬT TRONG CÂU BÁO CHÍ ============

# Mẫu chữ hoa tiếng Việt (Case-sensitive!)
VN_CAP_WORD = (
    r"[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ"
    r"ÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
    r"[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    r"ùúụủũưừứựửữỳýỵỷỹđ']*"
)

# Các từ mở đầu một cụm chức danh chính trị
ROLE_STARTERS = [
    "tổng bí thư", "nguyên tổng bí thư",
    "chủ tịch nước", "phó chủ tịch nước", "nguyên chủ tịch nước", "nguyên phó chủ tịch nước",
    "thủ tướng chính phủ", "thủ tướng", "phó thủ tướng thường trực chính phủ",
    "phó thủ tướng thường trực", "phó thủ tướng chính phủ", "phó thủ tướng",
    "nguyên thủ tướng", "nguyên phó thủ tướng",
    "chủ tịch quốc hội", "phó chủ tịch thường trực quốc hội", "phó chủ tịch quốc hội",
    "nguyên chủ tịch quốc hội", "nguyên phó chủ tịch quốc hội",
    "thường trực ban bí thư", "ủy viên thường vụ bộ chính trị", "ủy viên bộ chính trị",
    "nguyên ủy viên bộ chính trị", "bí thư trung ương đảng", "bí thư tw đảng",
    "ủy viên dự khuyết trung ương đảng", "ủy viên dự khuyết bch trung ương đảng",
    "ủy viên dự khuyết ban chấp hành trung ương đảng",
    "ủy viên ban chấp hành trung ương đảng", "ủy viên bch trung ương đảng",
    "ủy viên trung ương đảng", "ủy viên tw đảng", "nguyên ủy viên trung ương đảng",
    "ủy viên thường vụ quân ủy trung ương", "ủy viên quân ủy trung ương", "phó bí thư quân ủy trung ương",
    "ủy viên ban thường vụ đảng ủy công an trung ương", "ủy viên thường vụ đảng ủy công an trung ương",
    "ủy viên ủy ban thường vụ quốc hội", "tổng thư ký quốc hội",
    "bộ trưởng, chủ nhiệm văn phòng chính phủ",
    "bộ trưởng", "thứ trưởng thường trực", "thứ trưởng", "quyền bộ trưởng",
    "nguyên bộ trưởng", "cựu bộ trưởng", "nguyên thứ trưởng", "cựu thứ trưởng",
    "thống đốc ngân hàng nhà nước", "thống đốc", "phó thống đốc",
    "tổng thanh tra chính phủ", "tổng thanh tra", "phó tổng thanh tra",
    "tổng kiểm toán nhà nước", "tổng kiểm toán", "phó tổng kiểm toán",
    "chánh án tòa án nhân dân", "chánh án tand", "chánh án", "phó chánh án",
    "viện trưởng viện kiểm sát", "viện trưởng vksnd", "viện trưởng", "phó viện trưởng",
    "trưởng ban", "phó trưởng ban thường trực", "phó trưởng ban",
    "chủ nhiệm ủy ban", "phó chủ nhiệm thường trực ủy ban", "phó chủ nhiệm ủy ban",
    "chủ nhiệm văn phòng", "phó chủ nhiệm văn phòng", "chủ nhiệm tổng cục chính trị",
    "phó chủ nhiệm tổng cục chính trị", "chủ nhiệm chính trị", "phó chủ nhiệm chính trị",
    "chủ nhiệm", "phó chủ nhiệm thường trực", "phó chủ nhiệm",
    "chánh văn phòng", "phó chánh văn phòng thường trực", "phó chánh văn phòng",
    "chánh thanh tra", "phó chánh thanh tra",
    "bí thư thứ nhất trung ương đoàn",
    "bí thư thành ủy", "phó bí thư thường trực thành ủy", "phó bí thư thành ủy",
    "bí thư tỉnh ủy", "phó bí thư thường trực tỉnh ủy", "phó bí thư tỉnh ủy",
    "bí thư đảng ủy", "phó bí thư thường trực đảng ủy", "phó bí thư đảng ủy",
    "bí thư huyện ủy", "phó bí thư huyện ủy", "bí thư quận ủy", "phó bí thư quận ủy",
    "bí thư thị ủy", "bí thư chi bộ", "bí thư", "phó bí thư thường trực", "phó bí thư",
    "nguyên bí thư", "cựu bí thư",
    "ủy viên ban thường vụ thành ủy", "ủy viên ban thường vụ tỉnh ủy",
    "ủy viên ban thường vụ đảng ủy", "ủy viên ban thường vụ", "ủy viên thường vụ",
    "ủy viên ủy ban kiểm tra", "ủy viên thường trực", "ủy viên chuyên trách", "ủy viên",
    "thành ủy viên", "tỉnh ủy viên", "đảng ủy viên",
    "chủ tịch ủy ban trung ương mttq", "phó chủ tịch ủy ban trung ương mttq",
    "chủ tịch ủy ban mttq", "phó chủ tịch thường trực ủy ban mttq", "phó chủ tịch ủy ban mttq",
    "chủ tịch ubnd", "phó chủ tịch thường trực ubnd", "phó chủ tịch ubnd",
    "chủ tịch ủy ban nhân dân", "phó chủ tịch thường trực ủy ban nhân dân", "phó chủ tịch ủy ban nhân dân",
    "chủ tịch hđnd", "phó chủ tịch thường trực hđnd", "phó chủ tịch hđnd",
    "chủ tịch hội đồng nhân dân", "phó chủ tịch thường trực hội đồng nhân dân", "phó chủ tịch hội đồng nhân dân",
    "chủ tịch hội đồng dân tộc", "phó chủ tịch hội đồng dân tộc",
    "chủ tịch", "phó chủ tịch thường trực", "phó chủ tịch", "nguyên chủ tịch", "cựu chủ tịch",
    "giám đốc sở", "phó giám đốc sở", "giám đốc công an", "phó giám đốc công an",
    "giám đốc", "phó giám đốc",
    "tổng cục trưởng", "phó tổng cục trưởng",
    "chi cục trưởng", "phó chi cục trưởng",
    "cục trưởng", "phó cục trưởng",
    "vụ trưởng", "phó vụ trưởng",
    "tổng tham mưu trưởng", "phó tổng tham mưu trưởng", "tham mưu trưởng",
    "tư lệnh", "phó tư lệnh", "chính ủy", "phó chính ủy", "chỉ huy trưởng", "phó chỉ huy trưởng",
    "trưởng đoàn đại biểu quốc hội", "phó trưởng đoàn đại biểu quốc hội",
    "trưởng đoàn đbqh", "phó trưởng đoàn đbqh", "đại biểu quốc hội",
    "đại tướng", "thượng tướng", "trung tướng", "thiếu tướng",
    "đô đốc", "phó đô đốc", "chuẩn đô đốc", "đại tá", "thượng tá",
]

SORTED_ROLE_STARTERS = sorted(set(ROLE_STARTERS), key=len, reverse=True)
ROLE_STARTERS_REGEX_STR = "|".join(re.escape(r) for r in SORTED_ROLE_STARTERS)
HONORIFICS_REGEX_STR = "|".join(re.escape(h) for h in sorted(HONORIFICS + ACADEMIC_RANKS, key=len, reverse=True))
PREFIX_TRIGGER_REGEX_STR = "|".join(
    re.escape(x) for x in sorted(set(ROLE_STARTERS + HONORIFICS + ACADEMIC_RANKS), key=len, reverse=True)
)


def strip_leading_geo_and_extract_name(pre_context: str, cap_words_str: str) -> tuple[str | None, str, str]:
    """
    Xử lý chuỗi từ viết hoa `cap_words_str` nằm sau `pre_context` (chức vụ + cơ quan):
    - Nếu `pre_context` kết thúc bằng xã/phường/thị trấn/huyện/quận/thị xã/đặc khu:
      Tách 2-3 từ đầu làm tên đơn vị hành chính, phần còn lại mới là tên người.
      Nếu tổng số từ <= 3 thì đó chỉ là tên địa danh (VD: "UBND xã Sơn Hồng"), trả về None!
    - Nếu `cap_words_str` bắt đầu bằng "Việt Nam" hoặc tên Tỉnh/Thành phố (VD: "Đà Nẵng Lê Ngọc Quang",
      "Gia Lai Thái Đại Ngọc", "Hà Nội Trần Đức Thắng"):
      Tách tên Tỉnh/Thành phố ra riêng và giữ phần tên người phía sau.
    Trả về: (clean_person_name, extracted_province, extra_local_unit)
    """
    words = cap_words_str.strip().split()
    if len(words) < 2:
        return None, "", ""

    pre_low = pre_context.lower().strip()
    extracted_prov = ""
    extra_local_unit = ""

    # Trường hợp 1: Ngay trước chuỗi viết hoa là cấp hành chính cơ sở (xã, phường, huyện, quận, thị xã, thị trấn, đặc khu)
    m_sub = re.search(r"\b(xã|phường|thị\s+trấn|huyện|quận|thị\s+xã|đặc\s+khu)\s*$", pre_low)
    if m_sub:
        unit_type = m_sub.group(1)
        if len(words) < 4:
            # Chỉ có tên xã/phường/huyện (2-3 từ), không có tên người phía sau
            return None, "", ""
        # Tìm vị trí tách: tên xã/phường thường dài 2 từ (hoặc 3 từ như Long Phú Thuận, Ô Chợ Dừa)
        for split_idx in (2, 3, 1):
            if split_idx < len(words):
                cand_person = " ".join(words[split_idx:])
                if is_valid_vn_politician_name(cand_person):
                    place_name = " ".join(words[:split_idx])
                    extra_local_unit = f"{unit_type} {place_name}"
                    return cand_person, extracted_prov, extra_local_unit
        return None, "", ""

    # Trường hợp 2: Bắt đầu bằng "Việt Nam" (VD: "Thủ tướng Việt Nam Lê Minh Hưng")
    if len(words) >= 4 and " ".join(words[:2]).lower() == "việt nam":
        words = words[2:]

    # Trường hợp 3: Bắt đầu bằng tên Tỉnh/Thành phố (VD: "Đà Nẵng Lê Ngọc Quang", "Gia Lai Thái Đại Ngọc")
    for p_len in (4, 3, 2, 1):
        if len(words) > p_len:
            prefix_str = " ".join(words[:p_len]).lower()
            if prefix_str in PROVINCE_ALIASES:
                extracted_prov = PROVINCE_ALIASES[prefix_str]
                words = words[p_len:]
                break

    # Kiểm tra xem phần còn lại có phải là chính tên Tỉnh/Thành phố không (nếu chỉ có tên tỉnh mà không có tên người)
    rem_str = " ".join(words)
    if rem_str.lower() in PROVINCE_ALIASES:
        return None, PROVINCE_ALIASES[rem_str.lower()], ""

    # Nếu chuỗi còn > 4 từ, thử tìm hậu tố 3-4 từ bắt đầu bằng Họ người Việt
    if not is_valid_vn_politician_name(rem_str) and len(words) >= 4:
        for tail_len in (4, 3):
            cand = " ".join(words[-tail_len:])
            if is_valid_vn_politician_name(cand):
                return cand, extracted_prov, extra_local_unit

    if is_valid_vn_politician_name(rem_str):
        return rem_str, extracted_prov, extra_local_unit

    return None, extracted_prov, extra_local_unit


def is_foreign_context(context_text: str) -> bool:
    """
    Kiểm tra xem cụm chức vụ/cơ quan có phải của quan chức nước ngoài hay không.
    (VD: "Bộ trưởng Bộ Tư pháp Trung Quốc", "Chủ tịch Quốc hội Lào", "Trợ lý Bộ trưởng Bộ Chiến tranh Hoa Kỳ")
    """
    if not context_text:
        return False
    c_low = context_text.lower()
    if FOREIGN_COUNTRY_REGEX.search(c_low):
        # Ngoại lệ: Đại sứ Việt Nam tại ..., Ủy ban Nhà nước về người Việt Nam ở nước ngoài...
        if "việt nam" in c_low:
            return False
        return True
    if any(k in c_low for k in ["tổng thống", "phó tổng thống", "thượng nghị sĩ", "hạ nghị sĩ", "nghị sĩ", "quốc vương", "nhà vua", "hoàng hậu", "thái tử", "công tước"]):
        return True
    return False


def split_post_nominal_clauses(post_text: str) -> list[str]:
    """
    Tách chuỗi chức danh nằm sau tên nhân vật (ngăn cách bởi dấu phẩy),
    nhưng giữ nguyên các dấu phẩy nằm trong tên cố định của Bộ/Ủy ban/Ban Chỉ đạo.
    """
    protected = protect_compound_commas(post_text)
    raw_parts = [p.strip() for p in protected.split(",") if p.strip()]
    clauses = []
    for part in raw_parts:
        restored = restore_compound_commas(part).strip()
        if not restored:
            continue
        # Nếu phần tiếp theo bắt đầu bằng một từ khóa chức vụ hoặc cơ quan Đảng/Nhà nước -> mệnh đề mới
        part_low = restored.lower()
        is_new_clause = any(
            part_low.startswith(k) for k in (
                SORTED_ROLE_STARTERS + [
                    "kiêm ", "nguyên ", "cựu ", "quyền ", "đảng ủy", "tỉnh ủy", "thành ủy",
                    "ủy ban", "ban ", "bộ ", "sở ", "cục ", "vụ ", "viện ", "quân khu",
                ]
            )
        )
        if is_new_clause or not clauses:
            clauses.append(restored)
        else:
            # Là phần tiếp nối của tên cơ quan dài phía trước
            clauses[-1] = f"{clauses[-1]}, {restored}"
    return clauses


def split_sentences(text: str) -> list[str]:
    """Tách văn bản bài báo thành danh sách các câu."""
    raw_sents = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in raw_sents if len(s.strip()) > 10]


def extract_quotes_from_sentence(sentence: str) -> list[str]:
    """Trích xuất câu nói trực tiếp trong dấu ngoặc kép "..." hoặc “...”."""
    quotes = re.findall(r'["\u201c]([^"\u201d]{20,350})["\u201d]', sentence)
    return [q.strip() for q in quotes]


def extract_age_and_hometown(sentence: str, person_name: str) -> tuple[int | None, str]:
    """Bóc tách tuổi/năm sinh và quê quán nằm trong ngoặc đơn sau tên nhân vật (nếu có)."""
    age = None
    hometown = ""
    pattern = re.escape(person_name) + r"\s*\(([^)]+)\)"
    match = re.search(pattern, sentence)
    if match:
        inside = match.group(1)
        age_m = re.search(r"(\d{2})\s*tuổi", inside, re.IGNORECASE)
        birth_m = re.search(r"(?:sn|sinh năm)\s*(\d{4})", inside, re.IGNORECASE)
        if age_m:
            age = int(age_m.group(1))
        elif birth_m:
            age = 2026 - int(birth_m.group(1))
        loc_m = re.search(r"(?:quê quán|quê|trú tại|ngụ tại)\s+([^,;)]+)", inside, re.IGNORECASE)
        if loc_m:
            hometown = loc_m.group(1).strip()
    return age, hometown


# ============ 7. HÀM LÕI: QUÉT BÀI BÁO & BÓC TÁCH CHÍNH TRỊ GIA VIỆT NAM ============

# Regex 1: Hậu tố chức vụ sau tên (Dấu phẩy hoặc dấu gạch ngang)
# VD: "Thượng tướng Nguyễn Văn Gấu, Ủy viên Trung ương Đảng, Thứ trưởng Bộ Quốc phòng..."
# VD: "ông Nguyễn Thái Nhàn - Đảng ủy viên, Bí thư Chi bộ, Chánh Văn phòng Ban Nội chính Thành ủy Hà Nội -"
PATTERN_NAME_THEN_ROLES = re.compile(
    rf"(?:(?P<pre_hon>(?i:{HONORIFICS_REGEX_STR}))\s+)?"
    rf"(?:(?P<pre_role>(?i:{ROLE_STARTERS_REGEX_STR}))\s+)?"
    rf"(?P<name>{VN_CAP_WORD}(?:\s+{VN_CAP_WORD}){{1,4}})"
    rf"\s*(?:,\s*|\s+[-–—]\s+|\s*\()"
    rf"(?P<post_roles>(?i:{ROLE_STARTERS_REGEX_STR})[^\.;!?\n\)]{{0,220}})"
)

# Regex 2: Tiền tố chuỗi Chức vụ (+ Cơ quan/Ban ngành/Tỉnh thành) đứng TRƯỚC Tên
# VD: "Ủy viên Bộ Chính trị, Bí thư Trung ương Đảng, Trưởng ban Tổ chức Trung ương Lê Minh Hưng"
# VD: "Thứ trưởng Bộ Nông nghiệp và Môi trường Lê Trọng Yên"
# VD: "Phó Chủ tịch Thường trực Ủy ban MTTQ Việt Nam thành phố Hà Nội Trần Thị Phương Hoa"
PATTERN_ROLES_THEN_NAME = re.compile(
    rf"(?:(?P<hon>(?i:{HONORIFICS_REGEX_STR}))\s+)?"
    rf"(?P<role_chain>(?i:{ROLE_STARTERS_REGEX_STR})(?:[^\.;:!?\n\(\)\-–—]{{0,110}}?))"
    rf"\s+(?P<cap_seq>{VN_CAP_WORD}(?:\s+{VN_CAP_WORD}){{1,6}})"
    rf"(?=\s+(?:[a-zà-ỹđ]|và\b|cùng\b)|[,.;:!?\)\-–—]|$)"
)

# Regex 3: Danh xưng (Đồng chí / Ông / Bà) + Tên (khi tên xuất hiện độc lập hoặc trong câu quyết định nhân sự)
PATTERN_HONORIFIC_NAME = re.compile(
    rf"\b(?P<hon>(?i:{HONORIFICS_REGEX_STR}))\s+"
    rf"(?P<name>{VN_CAP_WORD}(?:\s+{VN_CAP_WORD}){{1,4}})"
    rf"(?=\s+[a-zà-ỹđ]|[,.;:!?\)\-–—]|$)"
)

# Regex 4: Mệnh đề bổ nhiệm / điều động / chuẩn y / bầu giữ chức trong câu
PATTERN_APPOINTMENT = re.compile(
    r"(?:giữ\s+chức(?:\s+vụ)?|bổ\s+nhiệm\s+giữ\s+chức|bầu\s+giữ\s+chức|thôi\s+giữ\s+chức(?:\s+vụ)?|"
    r"tham\s+gia\s+Ban\s+Chấp\s+hành,\s*Ban\s+Thường\s+vụ(?:\s+và\s+giữ\s+chức)?|"
    r"tham\s+gia\s+Ủy\s+ban\s+Kiểm\s+tra|"
    r"nhận\s+công\s+tác\s+tại|điều\s+động\s+đến\s+công\s+tác\s+tại)\s+([^\.;!\?\n]{3,120})",
    re.IGNORECASE
)


def extract_persons_from_article(article: dict) -> list[dict]:
    """
    Quét toàn bộ 1 bài báo, nhận diện các CHÍNH TRỊ GIA VIỆT NAM và bóc tách đầy đủ:
      - Chức vụ (role_title / roles_list)
      - Ban ngành (ban_nganh / ban_nganh_list)
      - Cơ quan (organization / organization_list)
      - Tỉnh thành (province / provinces_list)
    """
    title_text = article.get("title", "") or ""
    sapo_text = article.get("sapo", "") or ""
    content_text = article.get("content", "") or ""
    full_text = f"{title_text}. {sapo_text}\n{content_text}"
    sentences = split_sentences(full_text)

    # Xác định tỉnh/thành phố chủ đạo của bài báo (từ Title và Sapo) để làm ngữ cảnh suy luận
    header_provinces = extract_provinces_from_text(f"{title_text}. {sapo_text}")
    article_default_province = header_provinces[0] if len(header_provinces) == 1 else ""

    persons_map = {}

    def ensure_person(name: str, honorific: str = "") -> dict:
        if name not in persons_map:
            persons_map[name] = {
                "person_name": name,
                "honorific": "",
                "roles": set(),
                "ban_nganh": set(),
                "organizations": set(),
                "provinces": set(),
                "age": None,
                "hometown": "",
                "quotes": [],
                "actions_context": [],
                "mention_count": 0,
            }
        p = persons_map[name]
        if honorific and not p["honorific"]:
            h_clean = honorific.strip().capitalize()
            if h_clean.lower() in ("đồng chí", "ông", "bà"):
                p["honorific"] = h_clean
        return p

    def attach_parsed_info(p: dict, parsed: dict):
        p["roles"].update(parsed["roles"])
        p["ban_nganh"].update(parsed["ban_nganh"])
        p["organizations"].update(parsed["organizations"])
        p["provinces"].update(parsed["provinces"])

    for sent in sentences:
        sent_provinces = extract_provinces_from_text(sent)
        sent_fallback_prov = sent_provinces[0] if len(sent_provinces) == 1 else article_default_province

        # --- BƯỚC 1A: Quét mẫu "Tên, Chức vụ 1, Chức vụ 2..." hoặc "Tên - Chức vụ 1, Chức vụ 2..." ---
        for m in PATTERN_NAME_THEN_ROLES.finditer(sent):
            pre_hon = m.group("pre_hon") or ""
            pre_role = m.group("pre_role") or ""
            raw_name = m.group("name").strip()
            post_roles_str = m.group("post_roles").strip()

            # Cắt tại dấu chấm phẩy hoặc gạch ngang đóng hoặc khi bắt đầu nhân vật tiếp theo
            post_roles_str = re.split(r"\s*;\s*|\s+[-–—]\s+|\s+cùng\s+các\s+đồng\s+chí|\s+và\s+(?:ông|bà|đồng\s+chí)\s+", post_roles_str)[0]

            if is_foreign_context(pre_role) or is_foreign_context(post_roles_str):
                continue

            clean_name, lead_prov, _ = strip_leading_geo_and_extract_name(pre_role, raw_name)
            if not clean_name:
                continue

            p = ensure_person(clean_name, honorific=pre_hon)
            if lead_prov:
                p["provinces"].add(lead_prov)

            if pre_role:
                attach_parsed_info(p, parse_political_clause(pre_role, fallback_province=lead_prov or sent_fallback_prov))

            for clause in split_post_nominal_clauses(post_roles_str):
                if not is_foreign_context(clause):
                    attach_parsed_info(p, parse_political_clause(clause, fallback_province=lead_prov or sent_fallback_prov))

        # --- BƯỚC 1B: Quét mẫu "Chuỗi Chức vụ + Cơ quan/Tỉnh thành + Tên" ---
        for m in PATTERN_ROLES_THEN_NAME.finditer(sent):
            hon = m.group("hon") or ""
            role_chain = m.group("role_chain").strip()
            cap_seq = m.group("cap_seq").strip()

            # Nếu trong role_chain có dấu chấm phẩy -> chỉ lấy phần sau dấu chấm phẩy cuối cùng
            if ";" in role_chain:
                role_chain = role_chain.split(";")[-1].strip()

            if is_foreign_context(role_chain):
                continue

            clean_name, lead_prov, extra_local_unit = strip_leading_geo_and_extract_name(role_chain, cap_seq)
            if not clean_name:
                continue

            # Kiểm tra xem ngay sau tên trong câu có phải là từ thuộc tên nước ngoài hoặc tổ chức không
            p = ensure_person(clean_name, honorific=hon)
            if lead_prov:
                p["provinces"].add(lead_prov)

            full_role_chain = f"{role_chain} {lead_prov}".strip() if lead_prov else role_chain
            if extra_local_unit:
                # Thay thế đơn vị xã/phường cụ thể vào role_chain
                full_role_chain = f"{role_chain} {extra_local_unit[len(extra_local_unit.split()[0]):].strip()}"

            for clause in split_post_nominal_clauses(full_role_chain):
                if not is_foreign_context(clause):
                    attach_parsed_info(p, parse_political_clause(clause, fallback_province=lead_prov or sent_fallback_prov))

        # --- BƯỚC 1C: Quét mẫu "Đồng chí / Ông / Bà + Tên" và kiểm tra mệnh đề bổ nhiệm/điều động trong câu ---
        for m in PATTERN_HONORIFIC_NAME.finditer(sent):
            hon = m.group("hon") or ""
            raw_name = m.group("name").strip()
            if not is_valid_vn_politician_name(raw_name):
                continue

            # Chỉ thêm hoặc cập nhật nếu trong câu có mệnh đề bổ nhiệm/chức vụ hoặc đã có mặt trong bài
            after_name_text = sent[m.end():]
            before_name_text = sent[:m.start()]

            # Nếu trước tên là ngữ cảnh nước ngoài -> bỏ qua
            if is_foreign_context(before_name_text[-40:]):
                continue

            has_appointment = False
            appointment_clauses = []
            for app_m in PATTERN_APPOINTMENT.finditer(after_name_text[:250]):
                has_appointment = True
                appointment_clauses.append(app_m.group(0))

            if has_appointment or raw_name in persons_map:
                p = ensure_person(raw_name, honorific=hon)
                for app_clause in appointment_clauses:
                    attach_parsed_info(p, parse_political_clause(app_clause, fallback_province=sent_fallback_prov))
                # Kiểm tra chủ thể ra quyết định ở đầu câu (VD: "Ban Thường vụ Thành ủy Hà Nội điều động ông...")
                if has_appointment and any(k in before_name_text.lower() for k in ["thành ủy", "tỉnh ủy", "ubnd", "bộ "]):
                    for p_prov in extract_provinces_from_text(before_name_text):
                        p["provinces"].add(p_prov)

    # --- BƯỚC 2: Thu thập số lần xuất hiện, ngữ cảnh hành động, phát ngôn cho từng nhân vật ---
    for name, p_info in list(persons_map.items()):
        for sent in sentences:
            if name in sent:
                p_info["mention_count"] += sent.count(name)
                if len(p_info["actions_context"]) < 3 and sent not in p_info["actions_context"]:
                    p_info["actions_context"].append(sent)

                if not p_info["age"] or not p_info["hometown"]:
                    age, hometown = extract_age_and_hometown(sent, name)
                    if age and not p_info["age"]:
                        p_info["age"] = age
                    if hometown and not p_info["hometown"]:
                        p_info["hometown"] = hometown
                        for hp in extract_provinces_from_text(hometown):
                            p_info["provinces"].add(hp)

                for q in extract_quotes_from_sentence(sent):
                    if q not in p_info["quotes"]:
                        p_info["quotes"].append(q)

                # Kiểm tra xem trong câu có mệnh đề bổ nhiệm/giữ chức gắn với nhân vật này không
                name_pos = sent.find(name)
                after_sub = sent[name_pos + len(name):name_pos + len(name) + 250]
                for app_m in PATTERN_APPOINTMENT.finditer(after_sub):
                    # Đảm bảo không vượt qua dấu chấm phẩy sang người khác
                    between = after_sub[:app_m.start()]
                    if ";" not in between:
                        attach_parsed_info(p_info, parse_political_clause(app_m.group(0), fallback_province=article_default_province))

    # --- BƯỚC 3: LỌC CHỈ GIỮ CHÍNH TRỊ GIA VIỆT NAM HỢP LỆ ---
    political_persons = {}
    for name, p_info in persons_map.items():
        if p_info["mention_count"] == 0:
            continue
        # Phải có ít nhất 1 chức vụ hoặc cơ quan/ban ngành chính trị
        if p_info["roles"] or p_info["organizations"] or p_info["ban_nganh"]:
            # Nếu vẫn chưa có tỉnh thành nhưng có cơ quan cấp tỉnh/thành/phường/xã và bài báo có tỉnh mặc định
            if not p_info["provinces"] and article_default_province:
                has_local_org = any(
                    any(k in o.lower() for k in ["tỉnh", "thành phố", "thành ủy", "tỉnh ủy", "ubnd", "hđnd", "sở ", "phường", "xã", "huyện", "quận"])
                    for o in p_info["organizations"]
                )
                if has_local_org:
                    p_info["provinces"].add(article_default_province)
            political_persons[name] = p_info

    # --- BƯỚC 4: Chuẩn hóa bản ghi đầu ra cấp Bài báo - Nhân vật ---
    co_names = sorted(political_persons.keys())
    result_rows = []
    for name, p_info in political_persons.items():
        roles_sorted = sorted(p_info["roles"])
        depts_sorted = sorted(p_info["ban_nganh"])
        orgs_sorted = sorted(p_info["organizations"])
        provs_sorted = sorted(p_info["provinces"])
        other_politicians = [n for n in co_names if n != name]

        loc_str = ", ".join(provs_sorted) if provs_sorted else p_info["hometown"]

        result_rows.append({
            "article_id": str(article.get("article_id", "")),
            "published_date": str(article.get("published_date", "")),
            "publisher": article.get("publisher", ""),
            "person_name": p_info["person_name"],
            "honorific": p_info["honorific"],
            "role_title": ", ".join(roles_sorted),
            "roles_list": roles_sorted,
            "ban_nganh": ", ".join(depts_sorted),
            "ban_nganh_list": depts_sorted,
            "department": ", ".join(depts_sorted),
            "organization": ", ".join(orgs_sorted),
            "organization_list": orgs_sorted,
            "co_quan": ", ".join(orgs_sorted),
            "province": ", ".join(provs_sorted),
            "provinces_list": provs_sorted,
            "tinh_thanh": ", ".join(provs_sorted),
            "location": loc_str,
            "age": p_info["age"],
            "mention_count": p_info["mention_count"],
            "is_main_character": False,
            "co_occurring_persons": other_politicians,
            "articles_present": [],       # Sẽ được tổng hợp ở Bước 2 toàn cục (Pass 2)
            "total_articles_count": 0,    # Sẽ được tổng hợp ở Bước 2 toàn cục (Pass 2)
            "quotes": p_info["quotes"],
            "actions_summary": " | ".join(p_info["actions_context"]),
            "article_title": title_text,
            "article_url": article.get("baomoi_url", article.get("original_url", "")),
        })

    result_rows.sort(key=lambda x: x["mention_count"], reverse=True)
    if result_rows:
        result_rows[0]["is_main_character"] = True

    return result_rows


# ============ 8. ĐỒNG BỘ HÓA HỒ SƠ CHÍNH TRỊ GIA TOÀN CỤC & XÂY DỰNG ĐỒ THỊ (PASS 2) ============

def consolidate_and_build_graph(all_records: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Pass 2 trên toàn bộ tập dữ liệu:
    1. Gom nhóm toàn bộ các bài báo có mặt (`articles_present`), chức vụ, ban ngành, cơ quan, tỉnh thành
       cho từng chính trị gia Việt Nam.
    2. Làm giàu ngược lại cho từng bản ghi bài báo nếu bài báo đó chỉ nhắc chức danh ngắn gọn
       (VD: chỉ ghi "Bộ trưởng Lương Tam Quang" thì tự động bổ sung Cơ quan "Bộ Công an", Ban ngành "Ngành Công an").
    3. Xuất ra bảng Hồ sơ Tổng hợp Chính trị gia (Nodes) và bảng Cạnh Quan hệ Đồng xuất hiện (Edges).
    """
    profiles = {}
    # Đếm tần suất xuất hiện của từng thuộc tính theo nhân vật để ưu tiên thông tin chuẩn xác nhất
    role_counts = defaultdict(Counter)
    dept_counts = defaultdict(Counter)
    org_counts = defaultdict(Counter)
    prov_counts = defaultdict(Counter)

    for rec in all_records:
        name = rec["person_name"]
        aid = str(rec["article_id"])
        if name not in profiles:
            profiles[name] = {
                "person_name": name,
                "honorific": rec["honorific"],
                "article_ids": [],
                "article_titles": [],
                "total_mentions": 0,
                "main_character_count": 0,
                "co_politicians": Counter(),
            }
        prof = profiles[name]
        if rec["honorific"] and not prof["honorific"]:
            prof["honorific"] = rec["honorific"]
        if aid not in prof["article_ids"]:
            prof["article_ids"].append(aid)
            if rec["article_title"]:
                prof["article_titles"].append(rec["article_title"])
        prof["total_mentions"] += rec["mention_count"]
        if rec["is_main_character"]:
            prof["main_character_count"] += 1

        for co_p in rec["co_occurring_persons"]:
            prof["co_politicians"][co_p] += 1

        for r in rec["roles_list"]:
            role_counts[name][r] += 1
        for d in rec["ban_nganh_list"]:
            dept_counts[name][d] += 1
        for o in rec["organization_list"]:
            org_counts[name][o] += 1
        for p in rec["provinces_list"]:
            prov_counts[name][p] += 1

    # Cập nhật ngược lại danh sách bài báo có mặt và làm giàu thông tin bị khuyết cho từng bản ghi
    for rec in all_records:
        name = rec["person_name"]
        prof = profiles[name]
        rec["articles_present"] = prof["article_ids"]
        rec["total_articles_count"] = len(prof["article_ids"])

        # Nếu nhân vật xuất hiện ở nhiều bài nhưng trong bài này bị khuyết ban_nganh / organization / province
        # (chỉ điền tự động khi nhân vật có cơ quan/tỉnh thành chủ đạo rõ ràng, tránh nhầm lẫn nếu trùng tên)
        if not rec["organization_list"] and org_counts[name]:
            top_orgs = [k for k, _ in org_counts[name].most_common(3)]
            rec["organization_list"] = sorted(top_orgs)
            rec["organization"] = ", ".join(rec["organization_list"])
            rec["co_quan"] = rec["organization"]

        if not rec["ban_nganh_list"] and dept_counts[name]:
            top_depts = [k for k, _ in dept_counts[name].most_common(3)]
            rec["ban_nganh_list"] = sorted(top_depts)
            rec["ban_nganh"] = ", ".join(rec["ban_nganh_list"])
            rec["department"] = rec["ban_nganh"]

        if not rec["provinces_list"] and len(prov_counts[name]) == 1:
            top_prov = [k for k, _ in prov_counts[name].most_common(1)]
            rec["provinces_list"] = top_prov
            rec["province"] = top_prov[0]
            rec["tinh_thanh"] = top_prov[0]
            if not rec["location"]:
                rec["location"] = top_prov[0]

    # Tạo danh sách Hồ sơ Tổng hợp Chính trị gia (Nodes)
    politician_nodes = []
    for name, prof in profiles.items():
        all_roles = [k for k, _ in role_counts[name].most_common()]
        all_depts = [k for k, _ in dept_counts[name].most_common()]
        all_orgs = [k for k, _ in org_counts[name].most_common()]
        all_provs = [k for k, _ in prov_counts[name].most_common()]
        top_co = [f"{k} ({v})" for k, v in prof["co_politicians"].most_common(15)]

        politician_nodes.append({
            "person_name": name,
            "honorific": prof["honorific"],
            "role_title": ", ".join(all_roles),
            "roles_list": all_roles,
            "ban_nganh": ", ".join(all_depts),
            "ban_nganh_list": all_depts,
            "organization": ", ".join(all_orgs),
            "organization_list": all_orgs,
            "province": ", ".join(all_provs),
            "provinces_list": all_provs,
            "total_articles": len(prof["article_ids"]),
            "total_mentions": prof["total_mentions"],
            "main_character_count": prof["main_character_count"],
            "co_occurring_degree": len(prof["co_politicians"]),
            "top_co_occurring_politicians": ", ".join(top_co),
            "article_ids": prof["article_ids"],
            "sample_article_titles": prof["article_titles"][:5],
        })

    politician_nodes.sort(key=lambda x: (x["total_articles"], x["total_mentions"]), reverse=True)

    # Tạo danh sách Cạnh Quan hệ Đồng xuất hiện (Edges)
    articles_to_persons = defaultdict(set)
    for rec in all_records:
        articles_to_persons[str(rec["article_id"])].add(rec["person_name"])

    pair_articles = defaultdict(list)
    for aid, p_set in articles_to_persons.items():
        if len(p_set) >= 2:
            for u, v in combinations(sorted(p_set), 2):
                pair_articles[(u, v)].append(aid)

    node_lookup = {n["person_name"]: n for n in politician_nodes}
    politician_edges = []
    for (u, v), shared_aids in pair_articles.items():
        u_info = node_lookup[u]
        v_info = node_lookup[v]
        shared_orgs = sorted(set(u_info["organization_list"]) & set(v_info["organization_list"]))
        shared_depts = sorted(set(u_info["ban_nganh_list"]) & set(v_info["ban_nganh_list"]))
        shared_provs = sorted(set(u_info["provinces_list"]) & set(v_info["provinces_list"]))

        politician_edges.append({
            "source_person": u,
            "target_person": v,
            "weight": len(shared_aids),
            "shared_article_ids": ", ".join(shared_aids),
            "shared_organizations": ", ".join(shared_orgs),
            "shared_ban_nganh": ", ".join(shared_depts),
            "shared_provinces": ", ".join(shared_provs),
        })

    politician_edges.sort(key=lambda x: x["weight"], reverse=True)
    return all_records, politician_nodes, politician_edges


# ============ 9. LƯU RA CƠ SỞ DỮ LIỆU SQLITE, JSON VÀ CSV ============

def save_to_sqlite(persons_rows: list[dict], politician_nodes: list[dict], politician_edges: list[dict], db_path: str):
    """Lưu cả 3 bảng (article_persons, politicians, politician_edges) vào SQLite để truy vấn đồ thị."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS article_persons")
    cursor.execute("DROP TABLE IF EXISTS politicians")
    cursor.execute("DROP TABLE IF EXISTS politician_edges")

    cursor.execute("""
        CREATE TABLE article_persons (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT,
            published_date TEXT,
            publisher TEXT,
            person_name TEXT,
            honorific TEXT,
            role_title TEXT,
            ban_nganh TEXT,
            organization TEXT,
            province TEXT,
            location TEXT,
            age INTEGER,
            mention_count INTEGER,
            is_main_character BOOLEAN,
            total_articles_count INTEGER,
            articles_present TEXT,
            co_occurring_persons TEXT,
            quotes TEXT,
            actions_summary TEXT,
            article_title TEXT,
            article_url TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE politicians (
            politician_id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT UNIQUE,
            honorific TEXT,
            role_title TEXT,
            ban_nganh TEXT,
            organization TEXT,
            province TEXT,
            total_articles INTEGER,
            total_mentions INTEGER,
            main_character_count INTEGER,
            co_occurring_degree INTEGER,
            top_co_occurring_politicians TEXT,
            article_ids TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE politician_edges (
            edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_person TEXT,
            target_person TEXT,
            weight INTEGER,
            shared_article_ids TEXT,
            shared_organizations TEXT,
            shared_ban_nganh TEXT,
            shared_provinces TEXT
        )
    """)

    cursor.execute("CREATE INDEX idx_ap_person ON article_persons(person_name)")
    cursor.execute("CREATE INDEX idx_ap_article ON article_persons(article_id)")
    cursor.execute("CREATE INDEX idx_ap_province ON article_persons(province)")
    cursor.execute("CREATE INDEX idx_pol_name ON politicians(person_name)")
    cursor.execute("CREATE INDEX idx_edge_src ON politician_edges(source_person)")
    cursor.execute("CREATE INDEX idx_edge_tgt ON politician_edges(target_person)")

    for row in persons_rows:
        cursor.execute("""
            INSERT INTO article_persons (
                article_id, published_date, publisher,
                person_name, honorific, role_title, ban_nganh, organization,
                province, location, age, mention_count, is_main_character,
                total_articles_count, articles_present, co_occurring_persons,
                quotes, actions_summary, article_title, article_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["article_id"], row["published_date"], row["publisher"],
            row["person_name"], row["honorific"], row["role_title"], row["ban_nganh"], row["organization"],
            row["province"], row["location"], row["age"], row["mention_count"], 1 if row["is_main_character"] else 0,
            row["total_articles_count"], ", ".join(row["articles_present"]), ", ".join(row["co_occurring_persons"]),
            json.dumps(row["quotes"], ensure_ascii=False), row["actions_summary"],
            row["article_title"], row["article_url"]
        ))

    for node in politician_nodes:
        cursor.execute("""
            INSERT INTO politicians (
                person_name, honorific, role_title, ban_nganh, organization,
                province, total_articles, total_mentions, main_character_count,
                co_occurring_degree, top_co_occurring_politicians, article_ids
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            node["person_name"], node["honorific"], node["role_title"], node["ban_nganh"], node["organization"],
            node["province"], node["total_articles"], node["total_mentions"], node["main_character_count"],
            node["co_occurring_degree"], node["top_co_occurring_politicians"], ", ".join(node["article_ids"])
        ))

    for edge in politician_edges:
        cursor.execute("""
            INSERT INTO politician_edges (
                source_person, target_person, weight,
                shared_article_ids, shared_organizations, shared_ban_nganh, shared_provinces
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            edge["source_person"], edge["target_person"], edge["weight"],
            edge["shared_article_ids"], edge["shared_organizations"], edge["shared_ban_nganh"], edge["shared_provinces"]
        ))

    conn.commit()
    conn.close()


def main():
    if not os.path.exists(INPUT_ARTICLES_JSON):
        print(f"[!] Không tìm thấy file '{INPUT_ARTICLES_JSON}'. Hãy chạy script thu thập bài báo trước.")
        return

    articles = []
    seen_article_ids = set()
    with open(INPUT_ARTICLES_JSON, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                art = json.loads(line)
                aid = str(art.get("article_id", ""))
                if aid and aid in seen_article_ids:
                    continue
                if aid:
                    seen_article_ids.add(aid)
                articles.append(art)
            except json.JSONDecodeError as e:
                print(f"[!] Lỗi parse JSON tại dòng {line_num}: {e}")

    print(f"[*] Đang phân tích và bóc tách CHÍNH TRỊ GIA VIỆT NAM từ {len(articles)} bài báo duy nhất...")
    all_person_records = []

    for idx, article in enumerate(articles, start=1):
        extracted = extract_persons_from_article(article)
        all_person_records.extend(extracted)
        if idx % 500 == 0 or idx == len(articles):
            print(f"  -> Đã xử lý {idx}/{len(articles)} bài báo | "
                  f"Bóc tách được {len(all_person_records)} hồ sơ lượt xuất hiện.")

    print("[*] Đang tổng hợp hồ sơ chính trị gia toàn cục (Chức vụ, Ban ngành, Cơ quan, Tỉnh thành, Bài báo có mặt)...")
    all_person_records, politician_nodes, politician_edges = consolidate_and_build_graph(all_person_records)

    # 1. Xuất bảng Nhân vật - Bài báo ra JSON
    with open(OUTPUT_PERSONS_JSON, "w", encoding="utf-8") as f_out:
        json.dump(all_person_records, f_out, ensure_ascii=False, indent=2)

    # 2. Xuất bảng Hồ sơ Tổng hợp Chính trị gia VN (Nodes) ra JSON
    with open(OUTPUT_PROFILES_JSON, "w", encoding="utf-8") as f_prof:
        json.dump(politician_nodes, f_prof, ensure_ascii=False, indent=2)

    # 3. Xuất ra Database SQLite (3 bảng liên kết phục vụ đồ thị)
    save_to_sqlite(all_person_records, politician_nodes, politician_edges, OUTPUT_SQLITE_DB)

    # 4. Xuất ra CSV để mở bằng Excel / Pandas / Gephi
    try:
        import pandas as pd

        df_records = pd.DataFrame(all_person_records)
        for col in ("roles_list", "ban_nganh_list", "organization_list", "provinces_list", "co_occurring_persons", "articles_present"):
            if col in df_records.columns:
                df_records[col] = df_records[col].apply(lambda v: ", ".join(v) if isinstance(v, list) else v)
        if "quotes" in df_records.columns:
            df_records["quotes"] = df_records["quotes"].apply(lambda q: " ; ".join(q) if isinstance(q, list) else q)
        df_records.to_csv(OUTPUT_PERSONS_CSV, index=False, encoding="utf-8-sig")

        df_nodes = pd.DataFrame(politician_nodes)
        for col in ("roles_list", "ban_nganh_list", "organization_list", "provinces_list", "article_ids", "sample_article_titles"):
            if col in df_nodes.columns:
                df_nodes[col] = df_nodes[col].apply(lambda v: " | ".join(v) if isinstance(v, list) else v)
        df_nodes.to_csv(OUTPUT_PROFILES_CSV, index=False, encoding="utf-8-sig")

        df_edges = pd.DataFrame(politician_edges)
        df_edges.to_csv(OUTPUT_EDGES_CSV, index=False, encoding="utf-8-sig")
    except ImportError:
        pass

    print(f"\n[HOÀN TẤT] Kết quả bóc tách Chính trị gia Việt Nam:")
    print(f"  - Tổng số lượt chính trị gia - bài báo : {len(all_person_records):,} bản ghi")
    print(f"  - Tổng số chính trị gia VN duy nhất     : {len(politician_nodes):,} người")
    print(f"  - Tổng số cạnh quan hệ đồng xuất hiện  : {len(politician_edges):,} cạnh")
    print(f"  - Bảng lượt xuất hiện (JSON/CSV)       : '{OUTPUT_PERSONS_JSON}', '{OUTPUT_PERSONS_CSV}'")
    print(f"  - Bảng hồ sơ Chính trị gia (Nodes)     : '{OUTPUT_PROFILES_JSON}', '{OUTPUT_PROFILES_CSV}'")
    print(f"  - Bảng cạnh Đồ thị (Edges)             : '{OUTPUT_EDGES_CSV}'")
    print(f"  - Cơ sở dữ liệu Đồ thị SQLite          : '{OUTPUT_SQLITE_DB}'")


if __name__ == "__main__":
    main()
