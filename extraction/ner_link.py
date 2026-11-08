"""NER + liên kết thực thể dựa trên gazetteer và luật (không dùng mô hình).

Thực thể trong một câu:
  ORG  – cơ quan: tên/alias trong gazetteer Wikipedia + mẫu cơ quan cấp tỉnh ("UBND tỉnh X", "Tỉnh ủy X", "Sở ... tỉnh X")
  PER  – người: chuỗi bắt đầu bằng họ tiếng Việt + 1–3 âm tiết viết hoa
         * khớp duy nhất 1 người trong gazetteer -> id Wikipedia
         * không có trong gazetteer nhưng đi kèm chức danh + cơ quan -> nút người mới (per:news:...)
  Chức danh đứng ngay trước/sau tên ("Bí thư Tỉnh ủy Nghệ An Nguyễn Đức Trung", "ông X, Chủ tịch UBND tỉnh Y")
  được phân tích thành các cặp (chức danh, cơ quan) -> cạnh GIU_CHUC_VU; cơ quan nằm trong cụm chức danh
  bị "hấp thụ" (không làm đối số quan hệ).
  Chức danh đứng một mình ("Thủ tướng yêu cầu ...") -> đồng tham chiếu tới người cuối cùng giữ chức danh đó trong bài.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from textnorm import norm_text, slug

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
CFG = ROOT / "config"

UP = "A-ZĐÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
LO = "a-zđàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
SYL = rf"[{UP}][{LO}]+"
B = r"(?<![\w])"   # biên trái
E = r"(?![\w])"    # biên phải

SURNAMES = ("Nguyễn Trần Lê Phạm Hoàng Huỳnh Phan Vũ Võ Đặng Bùi Đỗ Hồ Ngô Dương Lý Đinh Đoàn Lương Trịnh Mai Đào "
            "Cao Lâm Tô Hà Tạ Chu Vương Thái Châu Kiều Lại Lưu Quách Triệu Đàm Hầu Giang Nông Lò Tống Thân Khuất "
            "Kim Từ Phùng Mạc Lã Nghiêm Doãn Bế Chẩu Sùng Hứa Diệp Quan Đậu Âu Tăng Lục Trương Lăng "
            "Danh Thạch Ksor Siu Rơ Y Nay Bạch Bành Ninh Khúc Mã Tôn Vi Lò Lường Cầm Giàng Mùa "
            "Thào Hờ Vàng Lầu Sầm Viên Ứng Thiều Kha Lỗ Tiêu Trình Uông").split()
NAME_RE = re.compile(B + r"(?:" + "|".join(sorted(set(SURNAMES), key=len, reverse=True)) + rf")(?: {SYL}){{1,3}}" + E)

# Chức danh (dài trước ngắn sau). Ánh xạ -> cơ quan ngầm định khi không có cơ quan theo sau.
IMPLICIT = {
    "Tổng Bí thư": "Ban Chấp hành Trung ương Đảng", "Thường trực Ban Bí thư": "Ban Bí thư",
    "Chủ tịch nước": "Chủ tịch nước", "Phó Chủ tịch nước": "Chủ tịch nước",
    "Thủ tướng": "Chính phủ", "Phó Thủ tướng Thường trực": "Chính phủ", "Phó Thủ tướng": "Chính phủ",
    "Bí thư Trung ương Đảng": "Ban Bí thư", "Ủy viên Trung ương Đảng": "Ban Chấp hành Trung ương Đảng",
    "Ủy viên dự khuyết Trung ương Đảng": "Ban Chấp hành Trung ương Đảng",
    "Tổng Thanh tra Chính phủ": "Thanh tra Chính phủ", "Phó Tổng Thanh tra Chính phủ": "Thanh tra Chính phủ",
    "Tổng Kiểm toán Nhà nước": "Kiểm toán Nhà nước", "Phó Tổng Kiểm toán Nhà nước": "Kiểm toán Nhà nước",
    "Thống đốc Ngân hàng Nhà nước": "Ngân hàng Nhà nước Việt Nam", "Phó Thống đốc Ngân hàng Nhà nước": "Ngân hàng Nhà nước Việt Nam",
}
BASE_TITLES = [
    "Ủy viên Thường vụ", "Ủy viên Ban Thường vụ", "Ủy viên Ủy ban Thường vụ", "Ủy viên", "Ủy viên Ban cán sự đảng",
    "Bí thư Đảng đoàn", "Bí thư Ban cán sự đảng", "Bí thư Đảng ủy", "Phó Bí thư Thường trực", "Phó Bí thư", "Bí thư",
    "Chủ tịch Hội đồng quản trị", "Chủ tịch HĐQT", "Phó Chủ tịch Thường trực", "Phó Chủ tịch", "Chủ tịch",
    "Chủ nhiệm", "Phó Chủ nhiệm Thường trực", "Phó Chủ nhiệm", "Trưởng ban", "Phó Trưởng ban Thường trực",
    "Phó Trưởng ban", "Trưởng Ban", "Phó Trưởng Ban", "Bộ trưởng", "Thứ trưởng Thường trực", "Thứ trưởng",
    "Quyền Bộ trưởng", "Tổng Giám đốc", "Phó Tổng Giám đốc", "Giám đốc", "Phó Giám đốc", "Chánh án", "Phó Chánh án",
    "Viện trưởng", "Phó Viện trưởng", "Tổng cục trưởng", "Phó Tổng cục trưởng", "Cục trưởng", "Phó Cục trưởng",
    "Vụ trưởng", "Phó Vụ trưởng", "Chánh Văn phòng", "Phó Chánh Văn phòng", "Tổng Thư ký", "Tổng Biên tập",
    "Phó Tổng Biên tập", "Chủ nhiệm Ủy ban Kiểm tra", "Phó Chủ nhiệm Ủy ban Kiểm tra", "Chánh Thanh tra",
    "Trưởng đoàn", "Phó Trưởng đoàn", "Trưởng Đoàn", "Phó Trưởng Đoàn", "Tư lệnh", "Phó Tư lệnh", "Chính ủy",
    "Phó Chính ủy", "Tham mưu trưởng", "Chỉ huy trưởng", "Đại biểu Quốc hội", "Người phát ngôn", "Đại sứ",
    "Thống đốc", "Phó Thống đốc", "Tổng Kiểm toán", "Phó Tổng Kiểm toán", "Tổng Thanh tra", "Phó Tổng Thanh tra",
    "Trưởng Công an", "Phó Trưởng Công an", "Thủ trưởng", "Trưởng", "Phó Trưởng", "Phó Chủ tịch nước",
]
RANKS = ["Đại tướng", "Thượng tướng", "Trung tướng", "Thiếu tướng", "Đô đốc", "Phó Đô đốc", "Chuẩn Đô đốc",
         "Đại tá", "Thượng tá", "Trung tá", "Thiếu tá", "Đại úy", "Giáo sư", "Phó Giáo sư", "GS", "PGS", "TS",
         "ThS", "GS.TS", "PGS.TS", "PGS. TS", "GS. TS", "Tiến sĩ", "Thạc sĩ", "Luật sư", "Bác sĩ", "Nhà báo",
         "Anh hùng Lao động", "Anh hùng Lực lượng vũ trang nhân dân"]
HONOR = r"(?:đồng chí|Đồng chí|ông|Ông|bà|Bà|các đồng chí|Các đồng chí)"
ALL_TITLES = sorted(set(BASE_TITLES) | set(IMPLICIT), key=len, reverse=True)
TITLE_ALT = "|".join(map(re.escape, ALL_TITLES))
RANK_ALT = "|".join(map(re.escape, sorted(RANKS, key=len, reverse=True)))
PRE = r"(?P<pre>(?:[Nn]guyên|[Qq]uyền|[Tt]ân|[Cc]ựu|[Cc]ố) )?"
TITLE_END_RE = re.compile(rf"(?:^|[\s,(]){PRE}(?P<t>{TITLE_ALT})\s*$")
TITLE_START_RE = re.compile(rf"^\s*{PRE}(?P<t>{TITLE_ALT}){E}")
RANK_HON_END_RE = re.compile(rf"(?:^|[\s,(])(?P<t>{RANK_ALT}|{HONOR})\s*$")
TITLE_ANY_RE = re.compile(rf"{B}(?P<t>{TITLE_ALT}){E}")
# Cụm "Thứ nhất", "khóa XV", "nhiệm kỳ 2020-2025" có thể chen giữa cơ quan và tên
FILLER_END_RE = re.compile(r"(?:,?\s*(?:khóa [IVXLC]+|nhiệm kỳ \d{4}\s*[-–]\s*\d{4}))\s*$")

PROV_KIND_WORD = r"(?:tỉnh|thành phố|Thành phố|TP\.?|Tp\.?)"
# Danh mục sở chuẩn (cũ + sau sắp xếp 2025); biến thể gạch nối được chuẩn hoá về dạng "và"
SO_NAMES = ["Nội vụ", "Tư pháp", "Tài chính", "Công Thương", "Công thương", "Nông nghiệp và Môi trường", "Xây dựng",
            "Khoa học và Công nghệ", "Khoa học - Công nghệ", "Khoa học-Công nghệ", "Giáo dục và Đào tạo", "Giáo dục - Đào tạo",
            "Y tế", "Văn hóa, Thể thao và Du lịch", "Văn hóa - Thể thao và Du lịch", "Văn hóa - Thể thao - Du lịch",
            "Văn hóa và Thể thao", "Du lịch", "Ngoại vụ", "Dân tộc và Tôn giáo", "Tài nguyên và Môi trường",
            "Tài nguyên - Môi trường", "Kế hoạch và Đầu tư", "Kế hoạch - Đầu tư", "Giao thông vận tải", "Giao thông Vận tải",
            "Thông tin và Truyền thông", "Lao động - Thương binh và Xã hội", "Lao động, Thương binh và Xã hội",
            "Nông nghiệp và Phát triển nông thôn", "Nông nghiệp - Phát triển nông thôn", "Quy hoạch - Kiến trúc",
            "Quy hoạch và Kiến trúc", "An toàn thực phẩm", "Giao thông công chính"]
SO_ALT = "|".join(map(re.escape, sorted(SO_NAMES, key=len, reverse=True)))
SO_CANON = {"Công thương": "Công Thương", "Khoa học - Công nghệ": "Khoa học và Công nghệ", "Khoa học-Công nghệ": "Khoa học và Công nghệ",
            "Giáo dục - Đào tạo": "Giáo dục và Đào tạo", "Văn hóa - Thể thao và Du lịch": "Văn hóa, Thể thao và Du lịch",
            "Văn hóa - Thể thao - Du lịch": "Văn hóa, Thể thao và Du lịch", "Tài nguyên - Môi trường": "Tài nguyên và Môi trường",
            "Kế hoạch - Đầu tư": "Kế hoạch và Đầu tư", "Giao thông Vận tải": "Giao thông vận tải",
            "Lao động, Thương binh và Xã hội": "Lao động - Thương binh và Xã hội",
            "Nông nghiệp - Phát triển nông thôn": "Nông nghiệp và Phát triển nông thôn", "Quy hoạch và Kiến trúc": "Quy hoạch - Kiến trúc"}
COUNTRIES = ("Nhật Bản|Hy Lạp|Lào|Campuchia|Trung Quốc|Hàn Quốc|Triều Tiên|Hoa Kỳ|Mỹ|Nga|Liên bang Nga|Pháp|Đức|Anh|Ấn Độ|"
             "Singapore|Thái Lan|Indonesia|Malaysia|Philippines|Australia|Úc|Cuba|Brazil|Ba Lan|Hungary|Séc|Italy|Italia|"
             "Tây Ban Nha|Bồ Đào Nha|Hà Lan|Bỉ|Thụy Sĩ|Thụy Điển|Na Uy|Phần Lan|Đan Mạch|Áo|Ukraine|Belarus|Kazakhstan|"
             "Mông Cổ|Myanmar|Brunei|Timor-Leste|Bangladesh|Pakistan|Iran|Israel|Ai Cập|Nam Phi|Nigeria|Algeria|Mozambique|"
             "Venezuela|Argentina|Chile|Mexico|Canada|New Zealand|Panama|Peru|Colombia|Thổ Nhĩ Kỳ|Saudi Arabia|UAE|Qatar|"
             "Kuwait|Angola|Uzbekistan|Azerbaijan|Armenia|Slovakia|Bulgaria|Romania|Serbia|Croatia|Slovenia|"
             "Luxembourg|Ireland|Sri Lanka|Nepal|Bhutan|Maldives|hai nước|nước bạn|các nước|ASEAN|EU|Liên minh châu Âu")
FOREIGN_AFTER_RE = re.compile(rf"\s+(?:nước |Vương quốc |Cộng hòa |Liên bang )?(?:{COUNTRIES})(?![\w])")
NOT_PERSON_BEFORE_RE = re.compile(r"(?:đường|Đường|phố|tuyến|cầu|Cầu|[Tt]rường|quảng trường|[Ll]ăng|[Bb]ảo tàng|tư tưởng|"
                                  r"di sản|[Tt]hành phố|TP\.?|Huân chương|[Gg]iải thưởng|[Kk]hu di tích|[Nn]hà văn hóa|"
                                  r"[Cc]ông viên|[Bb]ến|[Kk]hu|Sân vận động|Bệnh viện|Đại lộ|đại lộ)\s*$")
BARE_UNIT = r"(?:Tỉnh ủy|Thành ủy|Ủy ban nhân dân tỉnh|Ủy ban nhân dân thành phố|UBND tỉnh|UBND thành phố|HĐND tỉnh|HĐND thành phố|Hội đồng nhân dân tỉnh|Đoàn ĐBQH tỉnh|Đoàn đại biểu Quốc hội tỉnh|Công an tỉnh|UBND|HĐND|tỉnh|thành phố)"
BARE_END_RE = re.compile(rf"(?<![\w])(?P<u>{BARE_UNIT})\s*$")
BARE_START_RE = re.compile(rf"^\s*(?P<u>{BARE_UNIT})(?![\w])")


@dataclass
class Mention:
    kind: str           # PER | ORG
    start: int
    end: int
    text: str
    id: str
    conf: float = 1.0
    absorbed: bool = False         # ORG nằm trong cụm chức danh của một người
    roles: list = field(default_factory=list)   # [(chức danh, org_id)] với PER
    via: str = ""                  # gazetteer | news | coref | title
    span: tuple = ()               # PER: phạm vi gồm cả cụm chức danh


class Linker:
    def __init__(self):
        # ---- tỉnh
        pc = json.loads((CFG / "provinces_2025.json").read_text(encoding="utf-8"))
        self.central = set(pc["central_cities"]) | {"Thành phố Hồ Chí Minh"}
        new_names = set(pc["merge"])
        old_names = {o for olds in pc["merge"].values() for o in olds}
        self.prov_alias = {norm_text(k): norm_text(v) for k, v in pc["aliases"].items()}
        self.prov_alias.update({"Hồ Chí Minh": "Thành phố Hồ Chí Minh", "HCM": "Thành phố Hồ Chí Minh",
                                "TP. HCM": "Thành phố Hồ Chí Minh", "TP. Hồ Chí Minh": "Thành phố Hồ Chí Minh",
                                "TP Hồ Chí Minh": "Thành phố Hồ Chí Minh", "Thừa Thiên-Huế": "Thừa Thiên Huế"})
        self.prov_id = {}
        for n in old_names:
            self.prov_id[n] = "prov:" + slug(n) + ("" if n in new_names else "_cu")
        for n in new_names:
            self.prov_id[n] = "prov:" + slug(n)
        self.prov_id["Thành phố Hồ Chí Minh"] = "prov:thanh_pho_ho_chi_minh"
        self.prov_status = {n: ("hiện hành" if n in new_names else "đã sáp nhập") for n in self.prov_id}
        names = set(self.prov_id) | set(self.prov_alias)
        self.prov_alt = "|".join(map(re.escape, sorted(names, key=len, reverse=True)))
        self.prov_any_re = re.compile(r"(?<![\w])(?:tỉnh|thành phố|Thành phố|TP\.?|Tp\.?|tại|ở|về|đến|của|và|Tỉnh|Tại)\s+(" + self.prov_alt + ")" + E)

        # ---- cơ quan (gazetteer)
        g_org = json.loads((PROC / "gazetteer_org.json").read_text(encoding="utf-8"))
        self.org_name = {}   # id -> tên hiển thị
        self.org_prov = {}
        for r in csv.DictReader((PROC / "nodes_org.csv").open(encoding="utf-8")):
            self.org_name[r["id"]] = r["name"]
            self.org_prov[r["id"]] = r.get("province") or ""
        self.org_lookup = {}  # tên chuẩn hoá (lower) -> id
        for name, oid in g_org.items():
            self.org_lookup[norm_text(name).lower()] = oid
        oc = json.loads((CFG / "org_mergers_2025.json").read_text(encoding="utf-8"))
        aliases = {norm_text(k): norm_text(v) for k, v in oc["aliases"].items()}
        aliases.update({
            "UBKT Trung ương": "Ủy ban Kiểm tra Trung ương", "MTTQ Việt Nam": "Ủy ban Trung ương Mặt trận Tổ quốc Việt Nam",
            "Ủy ban Trung ương MTTQ Việt Nam": "Ủy ban Trung ương Mặt trận Tổ quốc Việt Nam",
            "Mặt trận Tổ quốc Việt Nam": "Ủy ban Trung ương Mặt trận Tổ quốc Việt Nam",
            "Bộ GD-ĐT": "Bộ Giáo dục và Đào tạo", "Bộ GD&ĐT": "Bộ Giáo dục và Đào tạo", "Bộ KH-CN": "Bộ Khoa học và Công nghệ",
            "Bộ KH&CN": "Bộ Khoa học và Công nghệ", "Bộ NN-MT": "Bộ Nông nghiệp và Môi trường",
            "Bộ NN&MT": "Bộ Nông nghiệp và Môi trường", "Bộ VH-TT-DL": "Bộ Văn hóa, Thể thao và Du lịch",
            "Bộ VHTT&DL": "Bộ Văn hóa, Thể thao và Du lịch", "Bộ DT-TG": "Bộ Dân tộc và Tôn giáo",
            "Bộ DT&TG": "Bộ Dân tộc và Tôn giáo", "TAND tối cao": "Tòa án nhân dân tối cao",
            "TAND Tối cao": "Tòa án nhân dân tối cao", "VKSND tối cao": "Viện kiểm sát nhân dân tối cao",
            "VKSND Tối cao": "Viện kiểm sát nhân dân tối cao", "Thường trực Chính phủ": "Chính phủ",
            "Thường vụ Quốc hội": "Ủy ban Thường vụ Quốc hội", "Thanh tra Chính phủ": "Thanh tra Chính phủ",
            "Ngân hàng Nhà nước": "Ngân hàng Nhà nước Việt Nam", "Đảng ủy Chính phủ": "Đảng ủy Chính phủ",
            "Đảng ủy Quốc hội": "Đảng ủy Quốc hội", "Văn phòng Trung ương Đảng": "Văn phòng Trung ương Đảng",
            "Ban Chấp hành Trung ương": "Ban Chấp hành Trung ương Đảng", "Trung ương Đảng": "Ban Chấp hành Trung ương Đảng",
            "Bộ Công Thương": "Bộ Công Thương", "Ủy ban Kiểm tra Trung ương Đảng": "Ủy ban Kiểm tra Trung ương",
            "KTNN": "Kiểm toán Nhà nước", "TTCP": "Thanh tra Chính phủ", "UBKTTW": "Ủy ban Kiểm tra Trung ương",
            "ĐHQG Hà Nội": "Đại học Quốc gia Hà Nội", "ĐHQGHN": "Đại học Quốc gia Hà Nội", "VPCP": "Văn phòng Chính phủ",
        })
        for k, v in aliases.items():
            vid = self.org_lookup.get(v.lower())
            if vid:
                self.org_lookup[k.lower()] = vid
        # tên quá chung chung -> bỏ
        bad = re.compile(r"^(Sở [^ ]+( [^ ]+)?|Ủy ban Kiểm tra( Đảng ủy)?|Đảng ủy|Ủy ban|Ban [^ ]+|Văn phòng|Hội đồng|"
                         r"Tổng cục [^ ]+|Cục [^ ]+|Vụ [^ ]+|Ủy ban nhân dân|Hội đồng nhân dân|Công an|Trường .*|"
                         r"Chủ tịch nước|Bộ đội.*)$")
        bad2 = re.compile(r"^(?:Tổng cục|Ủy ban nhân dân (?:tỉnh|thành phố)|Hội đồng nhân dân (?:tỉnh|thành phố)|Học viện Chính trị|"
                          r"(?:Bộ trưởng|Thứ trưởng|Chủ tịch|Phó Chủ tịch|Giám đốc|Phó Giám đốc|Trưởng|Phó|Tổng|Chánh|Bí thư|Ủy viên)\b(?! (?:Liên|Kiểm toán|Thanh tra|cục|Công ty|Tham mưu))).*$")
        org_names = [n for n in self._display_names(g_org, aliases) if len(n) >= 6 and not bad.match(n) and not bad2.match(n)
                     and "," not in n]
        org_names.sort(key=len, reverse=True)
        self.org_re = re.compile(B + "(" + "|".join(map(re.escape, org_names)) + ")" + E, re.IGNORECASE)

        # ---- cơ quan cấp tỉnh theo mẫu
        P = rf"(?P<p>{self.prov_alt})"
        self.prov_body_re = re.compile(
            B + r"(?P<body>Ủy ban nhân dân|UBND|Hội đồng nhân dân|HĐND|Công an|Bộ Chỉ huy Quân sự|"
                r"Ủy ban Mặt trận Tổ quốc Việt Nam|Ủy ban MTTQ Việt Nam|Ủy ban MTTQ|Đoàn đại biểu Quốc hội|Đoàn ĐBQH|"
                r"Tòa án nhân dân|TAND|Viện kiểm sát nhân dân|VKSND|Thanh tra|Văn phòng UBND|Văn phòng Ủy ban nhân dân|"
                r"Sở (?:" + SO_ALT + r")|Ban Quản lý (?:Khu kinh tế|các [Kk]hu công nghiệp|[Kk]hu công nghệ cao|[Dd]ự án (?:(?!được|trình|là|để|làm|và U|và Ủ|của|cho|tại|đề nghị|đề xuất|báo cáo|gửi|phối hợp|khu vực [A-ZĐ])[^,.;:()]){3,45}?))"
            + rf"\s+{PROV_KIND_WORD}\s*{P}" + E + r"|"
            + B + r"(?P<body2>UBND|HĐND|Công an|Thành ủy|Ủy ban Kiểm tra Thành ủy)\s+(?P<p2>TP\.? ?HCM|TPHCM)" + E)
        self.party_re = re.compile(
            B + r"(?P<pre>Ủy ban Kiểm tra |Ban Tổ chức |Ban Tuyên giáo và Dân vận |Ban Tuyên giáo |Ban Dân vận |"
                r"Ban Nội chính |Văn phòng |Ban Thường vụ |Ban Chấp hành Đảng bộ |Thường trực )?"
            + rf"(?P<k>Tỉnh ủy|Thành ủy|Đảng bộ tỉnh|Đảng bộ thành phố)\s+{P}" + E)
        self.new_orgs: dict[str, dict] = {}       # id -> {name,type,level,province}
        self.new_org_edges: list[tuple] = []      # (src, rel, dst, dst_label)

        # ---- người
        g_per = json.loads((PROC / "gazetteer_person.json").read_text(encoding="utf-8"))
        self.per_lookup = {}
        for name, lst in g_per.items():
            n = norm_text(name)
            ids = {x["id"] for x in lst}
            self.per_lookup.setdefault(n, set()).update(ids)
        self.per_name = {r["id"]: r["name"] for r in csv.DictReader((PROC / "nodes_person.csv").open(encoding="utf-8"))}
        self.per_orgs: dict[str, set] = {}
        for r in csv.DictReader((PROC / "edges_wiki.csv").open(encoding="utf-8")):
            if r["rel"] == "GIU_CHUC_VU":
                self.per_orgs.setdefault(r["src"], set()).add(r["dst"])
        self.new_persons: dict[str, dict] = {}

    @staticmethod
    def _display_names(g_org, aliases):
        names = {norm_text(n) for n in g_org}
        names |= set(aliases)
        return names

    # ------------------------------------------------------------ helpers
    def canon_prov(self, p: str) -> str:
        p = re.sub(r"\s+", " ", p.strip())
        if re.fullmatch(r"TP\.? ?HCM|TPHCM", p):
            return "Thành phố Hồ Chí Minh"
        return self.prov_alias.get(p, p)

    def _org_by_name(self, name: str, typ: str, prov: str | None, parent: str | None = None) -> str:
        oid = self.org_lookup.get(name.lower())
        if oid:
            return oid
        oid = "org:" + slug(name)
        if oid not in self.new_orgs and oid not in self.org_name:
            self.new_orgs[oid] = {"id": oid, "name": name, "type": typ, "level": "Tỉnh" if prov else "TW",
                                  "province": prov or ""}
            if prov:
                self.new_org_edges.append((oid, "THUOC_DIA_PHUONG", self.prov_id.get(prov, "prov:" + slug(prov)), "Province"))
            if parent and parent != oid:
                self.new_org_edges.append((oid, "TRUC_THUOC", parent, "Organization"))
        self.org_lookup[name.lower()] = oid
        return oid

    def _prov_org(self, body: str, prov: str) -> tuple[str, str]:
        kind = "thành phố" if prov in self.central else "tỉnh"
        pname = prov if prov != "Thành phố Hồ Chí Minh" else "Hồ Chí Minh"
        body = {"UBND": "Ủy ban nhân dân", "HĐND": "Hội đồng nhân dân", "Ủy ban MTTQ Việt Nam": "Ủy ban Mặt trận Tổ quốc Việt Nam",
                "Ủy ban MTTQ": "Ủy ban Mặt trận Tổ quốc Việt Nam", "Đoàn ĐBQH": "Đoàn đại biểu Quốc hội",
                "TAND": "Tòa án nhân dân", "VKSND": "Viện kiểm sát nhân dân",
                "Văn phòng UBND": "Văn phòng Ủy ban nhân dân"}.get(body, body)
        if body.startswith("Sở "):
            body = "Sở " + SO_CANON.get(body[3:], body[3:])
        body = body.replace("Ban Quản lý các Khu công nghiệp", "Ban Quản lý các khu công nghiệp").replace("Ban Quản lý dự án Đầu tư", "Ban Quản lý dự án đầu tư")
        name = f"{body} {kind} {pname}"
        typ = {"Ủy ban nhân dân": "UBND tỉnh", "Hội đồng nhân dân": "HĐND tỉnh", "Công an": "Công an tỉnh",
               "Đoàn đại biểu Quốc hội": "Đoàn ĐBQH tỉnh", "Tòa án nhân dân": "Cơ quan tư pháp",
               "Viện kiểm sát nhân dân": "Cơ quan tư pháp", "Bộ Chỉ huy Quân sự": "Lực lượng vũ trang",
               "Ủy ban Mặt trận Tổ quốc Việt Nam": "Mặt trận & đoàn thể"}.get(body, "Sở" if body.startswith("Sở ") else "Cơ quan cấp tỉnh")
        parent = None
        if body.startswith("Sở ") or body.startswith("Văn phòng") or body.startswith("Ban Quản lý") or body == "Thanh tra":
            parent = self._prov_org("Ủy ban nhân dân", prov)[0]
        elif body == "Công an":
            parent = self.org_lookup.get("bộ công an")
        elif body == "Bộ Chỉ huy Quân sự":
            parent = self.org_lookup.get("bộ quốc phòng")
        return self._org_by_name(name, typ, prov, parent), name

    def _party_org(self, pre: str, k: str, prov: str) -> tuple[str, str]:
        unit = "Thành ủy" if prov in self.central else "Tỉnh ủy"
        pname = prov if prov != "Thành phố Hồ Chí Minh" else "Thành phố Hồ Chí Minh"
        base = f"{unit} {pname}"
        pre = (pre or "").strip()
        if pre in ("", "Ban Thường vụ", "Ban Chấp hành Đảng bộ", "Thường trực"):
            return self._org_by_name(base, "Cấp ủy tỉnh", prov), base
        parent = self._org_by_name(base, "Cấp ủy tỉnh", prov)
        name = f"{pre} {base}"
        return self._org_by_name(name, "Cơ quan Đảng tỉnh", prov, parent), name

    # ------------------------------------------------------------ nhận diện
    def find_orgs(self, s: str) -> list[Mention]:
        ms = []
        for m in re.finditer(r"(?<![\w])Thanh tra (Bộ [^,.;:()]{2,45}?)(?=[,.;:()]|\s+(?:đã|vừa|ban hành|công bố|kết luận|thanh tra|tiến hành|cho biết|và|có|sẽ|tổ chức)\b)", s):
            parent = self.org_lookup.get(norm_text(m.group(1)).lower())
            if parent:
                pname = self.org_name.get(parent) or m.group(1)
                oid = self._org_by_name("Thanh tra " + re.sub(r" Việt Nam$", "", pname), "Đơn vị thuộc bộ", None, parent)
                ms.append(Mention("ORG", m.start(), m.end(), m.group(0), oid))
        for m in self.party_re.finditer(s):
            prov = self.canon_prov(m.group("p"))
            oid, name = self._party_org(m.group("pre"), m.group("k"), prov)
            ms.append(Mention("ORG", m.start(), m.end(), m.group(0), oid))
        for m in self.prov_body_re.finditer(s):
            if m.group("body"):
                body, prov = m.group("body").strip(), self.canon_prov(m.group("p"))
            else:
                body, prov = m.group("body2"), "Thành phố Hồ Chí Minh"
                if body == "Ủy ban Kiểm tra Thành ủy":
                    oid, _ = self._party_org("Ủy ban Kiểm tra ", "Thành ủy", prov)
                    ms.append(Mention("ORG", m.start(), m.end(), m.group(0), oid)); continue
                if body == "Thành ủy":
                    oid, _ = self._party_org("", "Thành ủy", prov)
                    ms.append(Mention("ORG", m.start(), m.end(), m.group(0), oid)); continue
            oid, name = self._prov_org(body, prov)
            ms.append(Mention("ORG", m.start(), m.end(), m.group(0), oid))
        for m in self.org_re.finditer(s):
            if not m.group(1)[0].isupper():
                continue
            oid = self.org_lookup.get(m.group(1).lower())
            if FOREIGN_AFTER_RE.match(s[m.end():]):
                continue  # Quốc hội Nhật Bản, Chính phủ Lào ...
            if re.match(r"\s+(?:phường|xã|huyện|quận|thị xã|thị trấn|cấp|các|tỉnh|thành phố|TP|[A-ZĐ][a-zđ]+ [A-ZĐ])", s[m.end():]) \
                    and oid and not oid.startswith(("org:bo_", "org:ban_", "org:chinh_phu", "org:quoc_hoi")):
                continue  # đơn vị cấp dưới / cơ quan khác cùng tiền tố (Hội LHPN phường X, Công an xã Y)
            if oid:
                ms.append(Mention("ORG", m.start(), m.end(), m.group(0), oid))
        return _dedup(ms)

    def find_persons_raw(self, s: str, blocked: list[Mention]) -> list[tuple[int, int, str]]:
        masked = list(s)
        for o in blocked:
            masked[o.start:o.end] = "#" * (o.end - o.start)
        for m in self.prov_any_re.finditer(s):
            masked[m.start(1):m.end(1)] = "#" * (m.end(1) - m.start(1))
        masked = "".join(masked)
        out = []
        for m in NAME_RE.finditer(masked):
            a, b = m.start(), m.end()
            parts = m.group(0).split()
            # tên dài 4 âm tiết mà 2–3 âm tiết đầu khớp gazetteer -> cắt (ví dụ "Phạm Minh Chính Chủ")
            if m.group(0) not in self.per_lookup:
                for k in range(len(parts) - 1, 1, -1):
                    if " ".join(parts[:k]) in self.per_lookup:
                        parts = parts[:k]
                        break
            name = " ".join(parts)
            out.append((a, a + len(name), name))
        return out

    def appositive_before(self, s: str, pos: int, orgs_by_end: dict[int, Mention]):
        """Phân tích ngược cụm chức danh trước tên tại pos -> (vị trí bắt đầu cụm, [(chức danh, org_id, mention)])."""
        roles, cur, start, chain = [], pos, pos, False
        for _ in range(8):
            seg = s[:cur]
            m = RANK_HON_END_RE.search(seg)
            if m:
                cur = start = m.start("t"); chain = True
                continue
            core = seg.rstrip()
            if chain and core.endswith(","):
                core = core[:-1].rstrip()
            fm = FILLER_END_RE.search(core)
            if fm:
                core = core[:fm.start()].rstrip()
            org = orgs_by_end.get(len(core))
            t_end = org.start if org else len(core)
            bare = None
            if not org:
                bm = BARE_END_RE.search(core)
                if bm:
                    bare, t_end = bm.group("u"), bm.start("u")
            tm = TITLE_END_RE.search(s[:t_end])
            if not tm or (not org and not bare and len(core) != tm.end("t") and s[tm.end("t"):len(core)].strip()):
                break
            roles.append((_role(tm, org), org.id if org else None, org) if not bare else (_role(tm, None), "BARE:" + bare, None))
            cur = start = tm.start("pre") if tm.group("pre") else tm.start("t"); chain = True
        return start, roles

    def appositive_after(self, s: str, end: int, orgs_by_start: dict[int, Mention]):
        roles, cur = [], end
        for _ in range(5):
            m = re.match(r"\s*,\s*", s[cur:])
            if not m:
                break
            p = cur + m.end()
            tm = TITLE_START_RE.match(s[p:])
            if not tm:
                break
            t_end = p + tm.end("t")
            sp = re.match(r"\s*", s[t_end:]).end()
            org = orgs_by_start.get(t_end + sp)
            if org:
                roles.append((_role(tm, org), org.id, org)); cur = org.end
                continue
            bm = BARE_START_RE.match(s[t_end:])
            if bm:
                roles.append((_role(tm, None), "BARE:" + bm.group("u"), None)); cur = t_end + bm.end()
                continue
            roles.append((_role(tm, None), None, None)); cur = t_end
        # cụm chức danh sau tên mà ngay sau đó là tên người khác -> thuộc người sau (danh sách), bỏ
        if roles and NAME_RE.match(s[cur:].lstrip(" ")) and not s[cur:].lstrip(" ").startswith((",", ";")):
            return end, []
        return cur, roles


def _role(tm, org) -> str:
    """Chức danh hiển thị: 'Trưởng' + 'Ban Tổ chức TW' -> 'Trưởng ban'; giữ tiền tố 'nguyên'."""
    t = tm.group("t")
    if t in ("Trưởng", "Phó Trưởng") and org is not None:
        t = t + " " + org.text.split()[0].lower()
    pre = (tm.group("pre") or "").strip().lower()
    pre = {"cựu": "nguyên", "cố": "nguyên"}.get(pre, pre)
    return (pre + " " + t) if pre else t


def _dedup(ms: list[Mention]) -> list[Mention]:
    """Giữ mention dài nhất khi chồng lấn."""
    ms.sort(key=lambda m: (-(m.end - m.start), m.start))
    keep = []
    for m in ms:
        if all(m.end <= k.start or m.start >= k.end for k in keep):
            keep.append(m)
    keep.sort(key=lambda m: m.start)
    return keep


class DocContext:
    """Trạng thái theo bài: tên người đã thấy -> id; (chức danh, cơ quan) -> người gần nhất."""

    def __init__(self):
        self.name2pid: dict[str, str] = {}
        self.title2pid: dict[tuple[str, str | None], str] = {}


def resolve_role_org(title: str, org_id: str | None, lk: Linker) -> str | None:
    if org_id == "org:ban_chap_hanh_trung_uong_dang" and title.endswith("Bí thư") and "Phó" not in title:
        return lk.org_lookup.get("ban bí thư", org_id)
    if org_id:
        return org_id
    imp = IMPLICIT.get(title)
    if imp:
        return lk.org_lookup.get(imp.lower())
    return None


def analyse_sentence(s: str, lk: Linker, ctx: DocContext) -> list[Mention]:
    orgs = lk.find_orgs(s)
    by_end = {o.end: o for o in orgs}
    by_start = {o.start: o for o in orgs}
    raw = lk.find_persons_raw(s, orgs)
    persons = []
    for a, b, name in raw:
        if NOT_PERSON_BEFORE_RE.search(s[max(0, a - 20):a]) or name in ("Hồ Chí Minh",) and "Chủ tịch Hồ Chí Minh" not in s:
            continue
        start, roles_b = lk.appositive_before(s, a, by_end)
        end, roles_a = lk.appositive_after(s, b, by_start)
        roles = roles_b + roles_a
        chain_prov = next((lk.org_prov.get(oid) or lk.new_orgs.get(oid, {}).get("province")
                           for _, oid, _ in roles if oid and not oid.startswith("BARE:")
                           and (lk.org_prov.get(oid) or lk.new_orgs.get(oid, {}).get("province"))), "")
        fixed = []
        for t, oid, om in roles:
            if oid and oid.startswith("BARE:"):
                u = oid[5:]
                oid = None
                if chain_prov:
                    if u in ("Tỉnh ủy", "Thành ủy"):
                        oid = lk._party_org("", u, chain_prov)[0]
                    elif u not in ("tỉnh", "thành phố"):
                        body = re.sub(r"\s*(tỉnh|thành phố)$", "", u)
                        oid = lk._prov_org(body, chain_prov)[0]
            fixed.append((t, resolve_role_org(t, oid, lk), om))
        roles = fixed
        has_title = bool(roles) or bool(RANK_HON_END_RE.search(s[:a]))
        n_syl = len(name.split())
        pid, via, conf = None, "", 1.0
        cands = lk.per_lookup.get(name)
        role_orgs = {r[1] for r in roles if r[1]}
        role_provs = {lk.org_prov.get(o) or lk.new_orgs.get(o, {}).get("province", "") for o in role_orgs} - {""}
        if name in ctx.name2pid:
            pid, via = ctx.name2pid[name], "doc"
        elif cands:
            hit = [c for c in cands if lk.per_orgs.get(c, set()) & role_orgs]
            if len(hit) == 1:
                pid, via = hit[0], "gazetteer+role"
            elif len(cands) == 1 and (n_syl >= 3 or has_title):
                c = next(iter(cands))
                c_provs = {lk.org_prov.get(o, "") for o in lk.per_orgs.get(c, set())} - {""}
                # chức vụ cấp tỉnh ở tỉnh mà người trong Wikipedia chưa từng công tác -> người khác trùng tên
                if not (role_provs and c_provs and not (role_provs & c_provs)):
                    pid, via = c, "gazetteer"
        if not pid and role_orgs and n_syl >= 3 and name not in ctx.name2pid:
            prov = next(iter(sorted(role_provs)), "")
            pid = "per:news:" + slug(name) + ("__" + slug(prov) if prov else "")
            via, conf = "news", 0.9
            lk.new_persons.setdefault(pid, {"id": pid, "name": name, "wiki_title": "", "wikidata": "",
                                            "birth_year": "", "hometown": "", "source": "news"})
        if not pid:
            continue
        ctx.name2pid[name] = pid
        for t, oid, om in roles:
            if om is not None:
                om.absorbed = True
            ctx.title2pid[(t, oid)] = pid
            if oid:
                ctx.title2pid.setdefault((t, None), pid)
        persons.append(Mention("PER", a, b, name, pid, conf=conf,
                               roles=[(t, oid) for t, oid, _ in roles if oid], via=via, span=(start, end)))
    # chức danh đứng một mình -> đồng tham chiếu
    covered = [p.span for p in persons]
    for m in TITLE_ANY_RE.finditer(s):
        a, b = m.start("t"), m.end("t")
        if any(x <= a < y for x, y in covered):
            continue
        t = m.group("t")
        if a > 0 and s[max(0, a - 7):a].strip().lower() in ("nguyên", "quyền", "tân", "cựu", "cố", "các", "những", "hai", "ba"):
            continue
        if re.search(r"(?:giữ chức|chức vụ|chức danh|các chức|chức|làm|vị trí|cương vị|bầu|bầu giữ chức|ứng cử|đề cử|"
                     r"phê chuẩn|bổ nhiệm|miễn nhiệm|thôi giữ chức|danh sách|là|nhiệm vụ|nguyên|và|hàm)\s*(?:đồng chí\s*)?$",
                     s[max(0, a - 25):a]):
            continue  # chức danh là nội dung (giữ chức Thủ tướng), không phải người
        sp = re.match(r"\s*", s[b:]).end()
        org = by_start.get(b + sp)
        nxt = s[(org.end if org else b):][:40]
        if NAME_RE.match(nxt.lstrip()) or re.match(r"\s*(các|những|cấp|của|hai|ba|nước)\b", nxt):
            continue
        if not org and re.match(rf"\s+[{UP}]", nxt) and not by_start.get(b + sp):
            continue  # "Thủ tướng Lào ...", "Chủ tịch Tập Cận Bình" -> không phải chức danh VN đứng một mình
        oid = resolve_role_org(t, org.id if org else None, lk)
        pid = ctx.title2pid.get((t, oid)) or (ctx.title2pid.get((t, None)) if not org else None)
        if pid and (t in IMPLICIT or org):
            if org:
                org.absorbed = True
            e = org.end if org else b
            persons.append(Mention("PER", a, e, s[a:e], pid, conf=0.85, via="coref", span=(a, e)))
            covered.append((a, e))
        elif not pid and t in IMPLICIT and not org and oid:
            # "Thủ tướng Chính phủ ban hành..." không rõ người -> coi là cơ quan ngầm định
            orgs.append(Mention("ORG", a, b, t, oid, conf=0.8, via="title"))
    for o in orgs:
        if any(p.span[0] <= o.start and o.end <= p.span[1] for p in persons):
            o.absorbed = True
    ments = sorted(orgs + persons, key=lambda x: x.start)
    return ments


def _org_prov(lk: Linker, oid: str) -> str:
    return lk.org_prov.get(oid, "")
