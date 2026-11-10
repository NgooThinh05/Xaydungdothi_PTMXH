import os
import re
import json
import time
import random
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup
import trafilatura
from tqdm import tqdm

# ==============================================================================
# 1. CẤU HÌNH DANH MỤC, TỪ KHÓA TÌM KIẾM & BỘ LỌC NỘI CHÍNH
# ==============================================================
BASE_URL = "https://baomoi.com"

# Các chuyên mục chính trên Báo Mới
CATEGORY_PATHS = [
    "/thoi-su.epi",
    "/chinh-tri.epi",
    "/xa-hoi.epi",
]

# ============ DANH SÁCH 34 TỈNH THÀNH VIỆT NAM (SAU SÁP NHẬP) ============
# Gồm 6 Thành phố trực thuộc Trung ương và 28 Tỉnh
CITIES_CENTRAL = {
    "Hà Nội", "TP.HCM", "Hải Phòng", "Đà Nẵng", "Huế", "Cần Thơ"
}

PROVINCES = [
    # 6 thành phố trực thuộc Trung ương
    "Hà Nội", "TP.HCM", "Hải Phòng", "Đà Nẵng", "Huế", "Cần Thơ",
    # Trung du và miền núi phía Bắc
    "Lào Cai", "Tuyên Quang", "Thái Nguyên", "Phú Thọ", "Lạng Sơn",
    "Cao Bằng", "Quảng Ninh", "Điện Biên", "Lai Châu", "Sơn La",
    # Đồng bằng sông Hồng
    "Bắc Ninh", "Hưng Yên", "Ninh Bình",
    # Bắc Trung Bộ & Duyên hải miền Trung
    "Thanh Hóa", "Nghệ An", "Hà Tĩnh", "Quảng Trị", "Quảng Ngãi",
    "Gia Lai", "Đắk Lắk", "Khánh Hòa", "Lâm Đồng",
    # Đông Nam Bộ
    "Đồng Nai", "Tây Ninh",
    # Đồng bằng sông Cửu Long
    "Đồng Tháp", "An Giang", "Vĩnh Long", "Cà Mau",
]

# ============ HỆ THỐNG CƠ QUAN TRUNG ƯƠNG (ĐẢNG, NHÀ NƯỚC, CHÍNH PHỦ, MẶT TRẬN) ============

# 1. Các Ban Đảng và Cơ quan trực thuộc Trung ương Đảng
CENTRAL_PARTY_ORGANS = [
    "Ban Chấp hành Trung ương",
    "Bộ Chính trị",
    "Ban Bí thư",
    "Văn phòng Trung ương Đảng",
    "Ban Tổ chức Trung ương",
    "Ủy ban Kiểm tra Trung ương",
    "Ban Tuyên giáo và Dân vận Trung ương", # Hợp nhất Tuyên giáo + Dân vận
    "Ban Nội chính Trung ương",
    "Ban Chính sách, chiến lược Trung ương", # Đổi tên từ Ban Kinh tế TW
    "Học viện Chính trị quốc gia Hồ Chí Minh",
    "Báo Nhân Dân",
    "Tạp chí Cộng sản",
    "Đảng ủy các cơ quan Đảng Trung ương",
    "Đảng ủy Chính phủ",
    "Đảng ủy Quốc hội",
    "Đảng ủy Mặt trận Tổ quốc, các đoàn thể Trung ương",
    "Quân ủy Trung ương",
    "Đảng ủy Công an Trung ương",
]

# 2. Chủ tịch nước, Quốc hội & Khối Tư pháp / Kiểm toán Trung ương
CENTRAL_STATE_NATIONAL_ASSEMBLY_JUDICIARY = [
    "Văn phòng Chủ tịch nước",
    "Quốc hội",
    "Ủy ban Thường vụ Quốc hội",
    "Văn phòng Quốc hội",
    "Hội đồng Dân tộc",
    "Ủy ban Pháp luật và Tư pháp",
    "Ủy ban Kinh tế và Tài chính",
    "Ủy ban Quốc phòng, An ninh và Đối ngoại",
    "Ủy ban Văn hóa và Xã hội",
    "Ủy ban Khoa học, Công nghệ và Môi trường",
    "Ủy ban Công tác đại biểu",
    "Ủy ban Dân nguyện và Giám sát",
    "Tòa án nhân dân tối cao",
    "Viện kiểm sát nhân dân tối cao",
    "Kiểm toán Nhà nước",
]

# 3. Chính phủ: 14 Bộ và 3 Cơ quan ngang Bộ (Sau hợp nhất, tinh gọn)
CENTRAL_MINISTRIES = [
    "Bộ Quốc phòng",
    "Bộ Công an",
    "Bộ Ngoại giao",
    "Bộ Nội vụ",                           # Hợp nhất Bộ Nội vụ + Bộ LĐ-TB&XH
    "Bộ Tư pháp",
    "Bộ Tài chính",                        # Hợp nhất Bộ Tài chính + Bộ KH&ĐT
    "Bộ Công Thương",
    "Bộ Nông nghiệp và Môi trường",        # Hợp nhất Bộ NN&PTNT + Bộ TN&MT
    "Bộ Xây dựng",                         # Hợp nhất Bộ Xây dựng + Bộ GTVT
    "Bộ Văn hóa, Thể thao và Du lịch",
    "Bộ Khoa học và Công nghệ",            # Hợp nhất Bộ KH&CN + Bộ TT&TT
    "Bộ Giáo dục và Đào tạo",
    "Bộ Y tế",
    "Bộ Dân tộc và Tôn giáo",              # Thành lập mới từ Ủy ban Dân tộc + Ban Tôn giáo CP
    # 3 Cơ quan ngang Bộ
    "Văn phòng Chính phủ",
    "Thanh tra Chính phủ",
    "Ngân hàng Nhà nước Việt Nam",
]

# 4. Các Cơ quan thuộc Chính phủ
GOVERNMENT_AGENCIES = [
    "Viện Hàn lâm Khoa học và Công nghệ Việt Nam",
    "Viện Hàn lâm Khoa học xã hội Việt Nam",
    "Đài Tiếng nói Việt Nam",
    "Đài Truyền hình Việt Nam",
    "Thông tấn xã Việt Nam",
]

# 5. Mặt trận Tổ quốc và các Tổ chức chính trị - xã hội Trung ương
CENTRAL_MASS_ORGANIZATIONS = [
    "Ủy ban Trung ương Mặt trận Tổ quốc Việt Nam",
    "Tổng Liên đoàn Lao động Việt Nam",
    "Trung ương Đoàn Thanh niên Cộng sản Hồ Chí Minh",
    "Trung ương Hội Liên hiệp Phụ nữ Việt Nam",
    "Trung ương Hội Nông dân Việt Nam",
    "Trung ương Hội Cựu chiến binh Việt Nam",
]

# ============ CÁC CẤP CƠ QUAN, SỞ, BAN, NGÀNH ĐỊA PHƯƠNG (TỈNH/THÀNH, XÃ/PHƯỜNG) ============
# (Không dùng chức danh cá nhân khi tìm kiếm; chỉ dùng tên các cấp cơ quan, ban, ngành, đoàn thể)

# 1. Danh sách các Sở, Ban, Ngành, Cơ quan chuyên môn dùng chung (ghép với từng tỉnh/thành)
PROVINCIAL_DEPARTMENTS = [
    # Khối các Sở chuyên môn thuộc UBND (mới hợp nhất & đặc thù)
    "Sở Tài chính",
    "Sở Xây dựng",
    "Sở Nông nghiệp và Môi trường",
    "Sở Khoa học và Công nghệ",
    "Sở Nội vụ",
    "Sở Y tế",
    "Sở Giáo dục và Đào tạo",
    "Sở Công Thương",
    "Sở Văn hóa, Thể thao và Du lịch",
    "Sở Văn hóa và Thể thao",
    "Sở Du lịch",
    "Sở Tư pháp",
    "Sở Dân tộc và Tôn giáo",
    "Sở Ngoại vụ",
    "Sở Quy hoạch - Kiến trúc",
    "Sở An toàn thực phẩm",
    # Các Sở tên cũ (quét các tin tức trước/trong quá trình sáp nhập & lịch sử công tác)
    "Sở Kế hoạch và Đầu tư",
    "Sở Giao thông vận tải",
    "Sở Tài nguyên và Môi trường",
    "Sở Nông nghiệp và Phát triển nông thôn",
    "Sở Thông tin và Truyền thông",
    "Sở Lao động - Thương binh và Xã hội",
    # Văn phòng, Thanh tra & các Ban Quản lý, Trung tâm cấp tỉnh/thành
    "Văn phòng UBND",
    "Văn phòng Đoàn ĐBQH và HĐND",
    "Ban Quản lý khu kinh tế",
    "Ban Quản lý các khu công nghiệp",
    "Ban Quản lý dự án đầu tư xây dựng",
    "Trung tâm Phục vụ hành chính công",
    "Trung tâm Phát triển quỹ đất",
    # Khối Cơ quan ngành dọc đóng tại địa phương
    "Chi cục Thuế khu vực",
    "Chi cục Hải quan khu vực",
    "Chi cục Quản lý thị trường",
    "Kho bạc Nhà nước",
    "Ngân hàng Nhà nước chi nhánh",
]

# 2. Danh sách các cấp Cơ quan, Ban Đảng, Chính quyền, Tư pháp, LLVT, Đoàn thể cấp Tỉnh (28 tỉnh)
LOCAL_SECTOR_ORGANS_PROVINCE = [
    # Cấp ủy Đảng & Chính quyền tỉnh
    "Tỉnh ủy", "Ban Thường vụ Tỉnh ủy", "Ban Chấp hành Đảng bộ tỉnh",
    "HĐND tỉnh", "Thường trực HĐND tỉnh", "UBND tỉnh",
    "Đoàn đại biểu Quốc hội tỉnh", "Ủy ban MTTQ tỉnh",
    "Đảng ủy các cơ quan Đảng tỉnh", "Đảng ủy UBND tỉnh",
    # Các Ban Đảng & Cơ quan thuộc Tỉnh ủy
    "Ban Tổ chức Tỉnh ủy", "Ủy ban Kiểm tra Tỉnh ủy",
    "Ban Nội chính Tỉnh ủy", "Ban Tuyên giáo và Dân vận Tỉnh ủy",
    "Ban Tuyên giáo Tỉnh ủy", "Ban Dân vận Tỉnh ủy",
    "Văn phòng Tỉnh ủy", "Trường Chính trị tỉnh",
    # Cơ quan Thanh tra, Tư pháp, Lực lượng vũ trang & Ngành dọc cấp tỉnh
    "Thanh tra tỉnh", "Công an tỉnh", "Đảng ủy Công an tỉnh",
    "Bộ Chỉ huy Quân sự tỉnh", "Đảng ủy Quân sự tỉnh", "Bộ đội Biên phòng tỉnh",
    "Tòa án nhân dân tỉnh", "Viện kiểm sát nhân dân tỉnh",
    "Cục Thi hành án dân sự tỉnh", "Cục Thuế tỉnh", "Cục Thống kê tỉnh",
    "Bảo hiểm xã hội tỉnh",
    # Mặt trận & Đoàn thể chính trị - xã hội cấp tỉnh
    "Liên đoàn Lao động tỉnh", "Tỉnh đoàn", "Hội Liên hiệp Phụ nữ tỉnh",
    "Hội Nông dân tỉnh", "Hội Cựu chiến binh tỉnh",
]

# 3. Danh sách các cấp Cơ quan, Ban Đảng, Chính quyền, Tư pháp, LLVT, Đoàn thể cấp Thành phố TW (6 TP)
LOCAL_SECTOR_ORGANS_CITY = [
    # Cấp ủy Đảng & Chính quyền thành phố
    "Thành ủy", "Ban Thường vụ Thành ủy", "Ban Chấp hành Đảng bộ thành phố",
    "HĐND thành phố", "Thường trực HĐND thành phố", "UBND thành phố",
    "Đoàn đại biểu Quốc hội thành phố", "Ủy ban MTTQ thành phố",
    "Đảng ủy các cơ quan Đảng thành phố", "Đảng ủy UBND thành phố",
    # Các Ban Đảng & Cơ quan thuộc Thành ủy
    "Ban Tổ chức Thành ủy", "Ủy ban Kiểm tra Thành ủy",
    "Ban Nội chính Thành ủy", "Ban Tuyên giáo và Dân vận Thành ủy",
    "Ban Tuyên giáo Thành ủy", "Ban Dân vận Thành ủy",
    "Văn phòng Thành ủy", "Trường Chính trị thành phố",
    # Cơ quan Thanh tra, Tư pháp, Lực lượng vũ trang & Ngành dọc cấp thành phố
    "Thanh tra thành phố", "Công an thành phố", "Đảng ủy Công an thành phố",
    "Bộ Tư lệnh thành phố", "Bộ Chỉ huy Quân sự thành phố", "Bộ đội Biên phòng thành phố",
    "Tòa án nhân dân thành phố", "Viện kiểm sát nhân dân thành phố",
    "Cục Thi hành án dân sự thành phố", "Cục Thuế thành phố", "Cục Hải quan thành phố",
    "Cục Thống kê thành phố", "Bảo hiểm xã hội thành phố",
    # Mặt trận & Đoàn thể chính trị - xã hội cấp thành phố
    "Liên đoàn Lao động thành phố", "Thành đoàn", "Hội Liên hiệp Phụ nữ thành phố",
    "Hội Nông dân thành phố", "Hội Cựu chiến binh thành phố",
]

# 4. Các cấp cơ quan Xã / Phường / Đặc khu & Cấp Huyện / Quận (Không dùng chức danh)
COMMUNE_AND_DISTRICT_ORGANS = [
    # Cấp xã / phường / đặc khu (Mô hình chính quyền địa phương 2 cấp)
    "Đảng ủy xã", "Ban Thường vụ Đảng ủy xã", "HĐND xã", "UBND xã",
    "Ủy ban MTTQ xã", "Công an xã", "Ban Chỉ huy Quân sự xã",
    "Đảng ủy phường", "Ban Thường vụ Đảng ủy phường", "HĐND phường", "UBND phường",
    "Ủy ban MTTQ phường", "Công an phường", "Ban Chỉ huy Quân sự phường",
    "Đảng ủy đặc khu", "HĐND đặc khu", "UBND đặc khu", "Công an đặc khu",
    # Cấp huyện / quận / thị xã (Dữ liệu lịch sử & cơ quan khu vực)
    "Huyện ủy", "Ban Thường vụ Huyện ủy", "HĐND huyện", "UBND huyện",
    "Ủy ban Kiểm tra Huyện ủy", "Ban Tổ chức Huyện ủy", "Thanh tra huyện",
    "Công an huyện", "Tòa án nhân dân huyện", "Viện kiểm sát nhân dân huyện",
    "Tòa án nhân dân khu vực", "Viện kiểm sát nhân dân khu vực",
    "Quận ủy", "Ban Thường vụ Quận ủy", "HĐND quận", "UBND quận",
    "Ủy ban Kiểm tra Quận ủy", "Công an quận", "Tòa án nhân dân quận", "Viện kiểm sát nhân dân quận",
    "Thị ủy", "UBND thị xã", "Phòng Tài nguyên và Môi trường", "Phòng Tài chính - Kế hoạch",
    "Phòng Giáo dục và Đào tạo", "Phòng Quản lý đô thị", "Phòng Kinh tế - Hạ tầng",
    "Văn phòng Đăng ký đất đai chi nhánh",
]


def generate_central_search_queries() -> list[str]:
    """
    Tự động sinh danh sách từ khóa tìm kiếm cấp Trung ương chỉ theo tên các cấp Ban, Bộ, Ngành,
    Cơ quan Trung ương (bỏ toàn bộ chức danh cá nhân).
    """
    queries = []
    seen = set()

    def add_query(q: str):
        q_clean = " ".join(q.split())
        if q_clean and q_clean not in seen:
            seen.add(q_clean)
            queries.append(q_clean)

    # 1. Các cơ quan Đảng Trung ương + hành động
    party_actions = [
        "Ban Chấp hành Trung ương ban hành nghị quyết",
        "Bộ Chính trị quyết định bổ nhiệm",
        "Bộ Chính trị điều động phân công",
        "Bộ Chính trị thi hành kỷ luật",
        "Ban Bí thư chỉ định",
        "Ban Bí thư điều động bổ nhiệm",
        "Ban Bí thư thi hành kỷ luật",
        "Văn phòng Trung ương Đảng thông báo",
        "Ban Tổ chức Trung ương công bố quyết định",
        "Ủy ban Kiểm tra Trung ương kiểm tra kỷ luật",
        "Ban Nội chính Trung ương theo dõi chỉ đạo",
        "Ban Tuyên giáo và Dân vận Trung ương quán triệt",
        "Ban Chính sách, chiến lược Trung ương làm việc",
        "Quân ủy Trung ương chỉ đạo",
        "Đảng ủy Công an Trung ương chỉ đạo",
        "Đảng ủy Chính phủ ban hành nghị quyết",
        "Đảng ủy Quốc hội làm việc",
        "Đảng ủy các cơ quan Đảng Trung ương",
        "Đảng ủy Mặt trận Tổ quốc, các đoàn thể Trung ương",
    ]
    for q in party_actions:
        add_query(q)

    # 2. Quốc hội, các Ủy ban của Quốc hội, Tư pháp & Kiểm toán tối cao
    for organ in CENTRAL_STATE_NATIONAL_ASSEMBLY_JUDICIARY:
        add_query(f"{organ} làm việc")
        add_query(f"{organ} giám sát")
    add_query("Ủy ban Thường vụ Quốc hội phê chuẩn")
    add_query("Tòa án nhân dân tối cao xét xử")
    add_query("Viện kiểm sát nhân dân tối cao truy tố")
    add_query("Kiểm toán Nhà nước kết luận kiến nghị")

    # 3. Chính phủ, 14 Bộ & 3 Cơ quan ngang Bộ
    add_query("Chính phủ ban hành nghị quyết")
    add_query("Chính phủ bổ nhiệm điều động")
    add_query("Văn phòng Chính phủ thông báo kết luận")
    add_query("Thanh tra Chính phủ công bố kết luận")
    for ministry in CENTRAL_MINISTRIES:
        add_query(f"{ministry} bổ nhiệm")
        add_query(f"{ministry} kiểm tra")
        add_query(f"{ministry} chỉ đạo")

    # 4. Các Cơ quan thuộc Chính phủ & Mặt trận, Đoàn thể Trung ương
    for agency in GOVERNMENT_AGENCIES + CENTRAL_MASS_ORGANIZATIONS:
        add_query(agency)

    # 5. Tập đoàn, Tổng công ty Nhà nước trọng điểm
    state_corporations = [
        "Tập đoàn Điện lực Việt Nam EVN",
        "Tập đoàn Công nghiệp - Năng lượng Quốc gia Petrovietnam",
        "Tập đoàn Công nghiệp Than - Khoáng sản TKV",
        "Tập đoàn Công nghiệp - Viễn thông Quân đội Viettel",
        "Tổng công ty Đầu tư và Kinh doanh vốn nhà nước SCIC",
    ]
    for corp in state_corporations:
        add_query(corp)

    return queries


def generate_provincial_search_queries() -> list[str]:
    """
    Tự động sinh danh sách từ khóa tìm kiếm địa phương CHỈ DÙNG CÁC CẤP BAN NGÀNH, CƠ QUAN
    (bỏ toàn bộ chức danh cá nhân):
    - 34 tỉnh/thành × Đầy đủ các cấp Ủy, Chính quyền, Ban Đảng, Tư pháp, LLVT, Đoàn thể
    - 34 tỉnh/thành × Đầy đủ các Sở, Ban, Ngành chuyên môn & Cơ quan ngành dọc
    - Các hoạt động theo từng lĩnh vực ban ngành địa phương & cấp xã/phường/đặc khu/huyện/quận.
    """
    queries = []
    seen = set()

    def add_query(q: str):
        q_clean = " ".join(q.split())
        if q_clean and q_clean not in seen:
            seen.add(q_clean)
            queries.append(q_clean)

    # --- Nhóm 1: Đầy đủ Cơ quan Đảng, Chính quyền, Tư pháp, LLVT, Đoàn thể × 34 tỉnh/thành ---
    for province in PROVINCES:
        is_city = province in CITIES_CENTRAL
        organs = LOCAL_SECTOR_ORGANS_CITY if is_city else LOCAL_SECTOR_ORGANS_PROVINCE
        for organ in organs:
            add_query(f"{organ} {province}")

    # --- Nhóm 2: Đầy đủ các Sở, Ban, Ngành chuyên môn & Ngành dọc × 34 tỉnh/thành ---
    for province in PROVINCES:
        is_city = province in CITIES_CENTRAL
        for dept in PROVINCIAL_DEPARTMENTS:
            # Các sở đặc thù chỉ có ở một số thành phố lớn
            if dept in ("Sở Quy hoạch - Kiến trúc", "Sở An toàn thực phẩm", "Sở Văn hóa và Thể thao", "Sở Du lịch") and not is_city:
                continue
            add_query(f"{dept} {province}")

    # --- Nhóm 3: Từ khóa hoạt động theo đầy đủ các lĩnh vực Ban Ngành địa phương (không chứa chức danh) ---
    sector_action_queries = [
        # Khối Đảng & Ban Tổ chức - Kiểm tra - Nội chính - Tuyên giáo Dân vận
        "Tỉnh ủy công bố quyết định nhân sự",
        "Tỉnh ủy điều động luân chuyển cán bộ",
        "Thành ủy công bố quyết định nhân sự",
        "Ban Thường vụ Tỉnh ủy chỉ đạo",
        "Ban Thường vụ Tỉnh ủy thi hành kỷ luật",
        "Ban Thường vụ Thành ủy quyết định",
        "Ban Tổ chức Tỉnh ủy công bố quyết định",
        "Ban Tổ chức Thành ủy công bố quyết định",
        "Ủy ban Kiểm tra Tỉnh ủy thi hành kỷ luật",
        "Ủy ban Kiểm tra Thành ủy kiểm tra kỷ luật",
        "Ban Nội chính Tỉnh ủy theo dõi chỉ đạo",
        "Ban Tuyên giáo và Dân vận Tỉnh ủy triển khai",
        "Đảng ủy các cơ quan Đảng tỉnh",
        "Đảng ủy UBND tỉnh công bố quyết định",
        # Khối Chính quyền (HĐND - UBND) & Sở Nội vụ - Thanh tra
        "HĐND tỉnh thông qua nghị quyết",
        "HĐND tỉnh kiện toàn nhân sự",
        "HĐND thành phố thông qua nghị quyết",
        "UBND tỉnh công bố quyết định bổ nhiệm",
        "UBND thành phố công bố quyết định bổ nhiệm",
        "UBND tỉnh điều động cán bộ",
        "UBND tỉnh kỷ luật cán bộ",
        "Sở Nội vụ công bố quyết định",
        "Thanh tra tỉnh công bố kết luận thanh tra",
        "Thanh tra thành phố chuyển hồ sơ công an",
        # Khối Kinh tế - Tài chính - Đầu tư - Công Thương - Thuế - Hải quan - Ngân hàng
        "Sở Tài chính thẩm định ngân sách",
        "Sở Kế hoạch và Đầu tư thu hồi dự án",
        "Sở Công Thương kiểm tra xử lý",
        "Ban Quản lý khu kinh tế cấp phép đầu tư",
        "Ban Quản lý các khu công nghiệp tỉnh",
        "Ban Quản lý dự án đầu tư xây dựng tỉnh",
        "Cục Thuế tỉnh cưỡng chế nợ thuế",
        "Chi cục Thuế khu vực",
        "Chi cục Hải quan khu vực",
        "Chi cục Quản lý thị trường kiểm tra",
        "Kho bạc Nhà nước tỉnh",
        "Ngân hàng Nhà nước chi nhánh tỉnh",
        # Khối Xây dựng - Giao thông - Quy hoạch - Nông nghiệp & Môi trường - Đất đai
        "Sở Xây dựng cấp phép kiểm tra",
        "Sở Giao thông vận tải xử lý",
        "Sở Quy hoạch - Kiến trúc thẩm định",
        "Sở Nông nghiệp và Môi trường kiểm tra",
        "Sở Tài nguyên và Môi trường thu hồi đất",
        "Trung tâm Phát triển quỹ đất giải phóng mặt bằng",
        "Văn phòng Đăng ký đất đai chi nhánh",
        # Khối Văn hóa - Giáo dục - Y tế - KH&CN - Tư pháp - Dân tộc Tôn giáo - BHXH
        "Sở Giáo dục và Đào tạo kiểm tra thanh tra",
        "Sở Y tế thanh tra xử phạt",
        "Sở Khoa học và Công nghệ chuyển đổi số",
        "Sở Văn hóa, Thể thao và Du lịch thanh tra",
        "Sở Tư pháp kiểm tra",
        "Sở Dân tộc và Tôn giáo triển khai",
        "Sở Ngoại vụ làm việc",
        "Sở Lao động - Thương binh và Xã hội",
        "Bảo hiểm xã hội tỉnh thanh tra",
        "Trung tâm Phục vụ hành chính công tỉnh",
        # Khối Công an - Quân sự - Biên phòng - Tòa án - Viện Kiểm sát - Thi hành án
        "Công an tỉnh khởi tố bắt tạm giam",
        "Công an thành phố khởi tố bắt giữ",
        "Công an tỉnh điều động bổ nhiệm",
        "Viện kiểm sát nhân dân tỉnh phê chuẩn truy tố",
        "Tòa án nhân dân tỉnh xét xử sơ thẩm",
        "Cục Thi hành án dân sự tỉnh",
        "Bộ Chỉ huy Quân sự tỉnh chỉ đạo",
        "Bộ đội Biên phòng tỉnh bắt giữ",
        # Khối Mặt trận Tổ quốc & Đoàn thể chính trị - xã hội địa phương
        "Ủy ban MTTQ tỉnh giám sát phản biện",
        "Liên đoàn Lao động tỉnh làm việc",
        "Tỉnh đoàn triển khai",
        "Hội Liên hiệp Phụ nữ tỉnh",
        "Hội Nông dân tỉnh",
        "Hội Cựu chiến binh tỉnh",
    ]
    for q in sector_action_queries:
        add_query(q)

    # --- Nhóm 4: Các cấp Ban Ngành Xã / Phường / Đặc khu & Cấp Huyện / Quận (không chứa chức danh) ---
    for organ in COMMUNE_AND_DISTRICT_ORGANS:
        add_query(organ)

    commune_district_queries = [
        "Đảng ủy phường chỉ đạo",
        "Đảng ủy xã làm việc",
        "Đảng ủy xã thi hành kỷ luật",
        "Đảng ủy đặc khu làm việc",
        "HĐND xã thông qua nghị quyết",
        "HĐND phường thông qua nghị quyết",
        "UBND phường chỉ đạo kiểm tra",
        "UBND phường kỷ luật cán bộ",
        "UBND xã chỉ đạo xử lý",
        "UBND xã kỷ luật cán bộ",
        "UBND xã vi phạm đất đai",
        "UBND đặc khu làm việc",
        "Công an phường khởi tố bắt giữ",
        "Công an xã điều tra xác minh",
        "Ủy ban MTTQ xã",
        "Ủy ban MTTQ phường",
        # Dữ liệu truy vết cơ quan cấp huyện/quận/thị xã & phòng ban chuyên môn
        "Huyện ủy chỉ đạo",
        "Ủy ban Kiểm tra Huyện ủy kỷ luật",
        "Quận ủy chỉ đạo",
        "UBND huyện chỉ đạo xử lý",
        "UBND huyện kỷ luật cán bộ",
        "UBND quận chỉ đạo kiểm tra",
        "UBND thị xã làm việc",
        "Thanh tra huyện kết luận",
        "Công an huyện khởi tố",
        "Công an quận khởi tố",
        "Tòa án nhân dân khu vực xét xử",
        "Viện kiểm sát nhân dân khu vực truy tố",
        "Phòng Tài nguyên và Môi trường huyện",
        "Phòng Tài chính - Kế hoạch huyện",
        "Phòng Giáo dục và Đào tạo huyện",
        "Phòng Quản lý đô thị",
    ]
    for q in commune_district_queries:
        add_query(q)

    return queries


# Sinh danh sách từ khóa cấp Trung ương và Địa phương
SEARCH_QUERIES_CENTRAL = generate_central_search_queries()
SEARCH_QUERIES_LOCAL = generate_provincial_search_queries()

# Gộp tất cả từ khóa
SEARCH_QUERIES = SEARCH_QUERIES_CENTRAL + SEARCH_QUERIES_LOCAL

# ============ BỘ TỪ KHÓA NHẬN DIỆN THỰC THỂ & QUAN HỆ CHÍNH TRỊ (LỌC NHIỄU) ============
POLITICAL_ENTITY_KEYWORDS = [
    # 1. Cấp Trung ương (Đảng, Nhà nước, Quốc hội, Chính phủ, Mặt trận)
    "tổng bí thư", "chủ tịch nước", "phó chủ tịch nước",
    "thủ tướng", "phó thủ tướng", "chủ tịch quốc hội", "phó chủ tịch quốc hội",
    "thường trực ban bí thư", "bộ chính trị", "ban bí thư", "ban chấp hành trung ương",
    "văn phòng trung ương đảng", "ban tổ chức trung ương", "ủy ban kiểm tra trung ương",
    "ban tuyên giáo và dân vận trung ương", "ban nội chính trung ương",
    "ban chính sách, chiến lược trung ương", "quân ủy trung ương", "đảng ủy công an trung ương",
    "ủy ban thường vụ quốc hội", "hội đồng dân tộc",
    "ủy ban pháp luật và tư pháp", "ủy ban kinh tế và tài chính",
    "ủy ban quốc phòng, an ninh và đối ngoại", "ủy ban văn hóa và xã hội",
    "ủy ban khoa học, công nghệ và môi trường", "ủy ban công tác đại biểu",
    "ủy ban dân nguyện và giám sát", "văn phòng quốc hội", "văn phòng chủ tịch nước",
    "tòa án nhân dân tối cao", "viện kiểm sát nhân dân tối cao", "kiểm toán nhà nước",
    "mặt trận tổ quốc", "tổng liên đoàn lao động", "trung ương đoàn",
    "hội liên hiệp phụ nữ", "hội nông dân", "hội cựu chiến binh",

    # 2. Các Bộ, Ngành (Cả tên mới sau hợp nhất và tên cũ phổ biến)
    "bộ trưởng", "thứ trưởng", "thống đốc", "tổng thanh tra", "cục trưởng", "vụ trưởng",
    "chính phủ", "văn phòng chính phủ", "thanh tra chính phủ", "ngân hàng nhà nước",
    "bộ quốc phòng", "bộ công an", "bộ ngoại giao", "bộ nội vụ", "bộ tư pháp",
    "bộ tài chính", "bộ công thương", "bộ nông nghiệp và môi trường",
    "bộ xây dựng", "bộ văn hóa, thể thao và du lịch", "bộ khoa học và công nghệ",
    "bộ giáo dục và đào tạo", "bộ y tế", "bộ dân tộc và tôn giáo",
    # Tên Bộ cũ (để bắt các bài báo nhắc lịch sử công tác)
    "bộ kế hoạch và đầu tư", "bộ giao thông vận tải", "bộ tài nguyên và môi trường",
    "bộ nông nghiệp và phát triển nông thôn", "bộ thông tin và truyền thông",
    "bộ lao động - thương binh và xã hội",

    # 3. Cấp Tỉnh / Thành phố (34 tỉnh thành - đầy đủ các Sở, Ban, Ngành, Đoàn thể, Tư pháp, LLVT)
    "tỉnh ủy", "thành ủy", "ban thường vụ tỉnh ủy", "ban thường vụ thành ủy",
    "hđnd tỉnh", "hđnd thành phố", "ubnd tỉnh", "ubnd thành phố",
    "đoàn đại biểu quốc hội", "ủy ban mttq tỉnh", "ủy ban mttq thành phố",
    "đảng ủy các cơ quan đảng", "đảng ủy ubnd",
    "bí thư tỉnh ủy", "bí thư thành ủy", "phó bí thư tỉnh ủy", "phó bí thư thành ủy",
    "chủ tịch ubnd tỉnh", "chủ tịch ubnd thành phố", "phó chủ tịch ubnd",
    "chủ tịch hđnd tỉnh", "chủ tịch hđnd thành phố", "phó chủ tịch hđnd",
    "giám đốc sở", "phó giám đốc sở", "chánh văn phòng ubnd", "chánh văn phòng tỉnh ủy", "chánh văn phòng thành ủy",
    "sở tài chính", "sở xây dựng", "sở nông nghiệp và môi trường",
    "sở khoa học và công nghệ", "sở nội vụ", "sở y tế", "sở giáo dục và đào tạo",
    "sở công thương", "sở văn hóa", "sở du lịch", "sở tư pháp", "sở dân tộc và tôn giáo",
    "sở ngoại vụ", "sở quy hoạch - kiến trúc", "sở an toàn thực phẩm",
    "sở kế hoạch và đầu tư", "sở giao thông vận tải", "sở tài nguyên và môi trường",
    "sở nông nghiệp và phát triển nông thôn", "sở thông tin và truyền thông",
    "sở lao động - thương binh và xã hội",
    "ban quản lý khu kinh tế", "ban quản lý các khu công nghiệp", "ban quản lý dự án",
    "trung tâm phục vụ hành chính công", "trung tâm phát triển quỹ đất",
    "giám đốc công an tỉnh", "giám đốc công an thành phố", "phó giám đốc công an",
    "công an tỉnh", "công an thành phố", "bộ chỉ huy quân sự", "bộ tư lệnh thành phố", "bộ đội biên phòng",
    "chánh thanh tra tỉnh", "chánh thanh tra thành phố", "thanh tra tỉnh", "thanh tra thành phố",
    "viện trưởng viện kiểm sát", "viện kiểm sát nhân dân tỉnh", "viện kiểm sát nhân dân thành phố",
    "chánh án tòa án", "tòa án nhân dân tỉnh", "tòa án nhân dân thành phố",
    "cục thi hành án dân sự", "cục thuế", "chi cục thuế", "cục hải quan", "chi cục hải quan",
    "chi cục quản lý thị trường", "bảo hiểm xã hội tỉnh", "bảo hiểm xã hội thành phố",
    "kho bạc nhà nước", "ngân hàng nhà nước chi nhánh", "cục thống kê",
    "ủy ban kiểm tra tỉnh ủy", "ủy ban kiểm tra thành ủy",
    "ban tổ chức tỉnh ủy", "ban tổ chức thành ủy",
    "ban nội chính tỉnh ủy", "ban nội chính thành ủy",
    "ban tuyên giáo và dân vận", "ban tuyên giáo tỉnh ủy", "ban dân vận tỉnh ủy",
    "liên đoàn lao động tỉnh", "liên đoàn lao động thành phố", "tỉnh đoàn", "thành đoàn",
    "hội liên hiệp phụ nữ tỉnh", "hội nông dân tỉnh", "hội cựu chiến binh tỉnh",


]

RELATION_TRIGGER_KEYWORDS = [
    "chủ trì", "chỉ đạo", "yêu cầu", "giao nhiệm vụ", "kết luận",       # DIRECTS
    "bổ nhiệm", "điều động", "luân chuyển", "phê chuẩn", "chỉ định",    # APPOINTS_TRANSFERS
    "hợp nhất", "sáp nhập", "tinh gọn", "kiện toàn", "sắp xếp",        # RESTRUCTURES
    "thanh tra", "kiểm tra", "giám sát", "kiểm toán", "vi phạm",        # INSPECTS_AUDITS
    "kỷ luật", "khiển trách", "cảnh cáo", "cách chức", "miễn nhiệm",    # DISCIPLINES_DISMISSES
    "cho thôi giữ chức", "nghỉ hưu trước tuổi", "xóa tư cách",          # RESIGNS_RETIRES
    "báo cáo", "kiến nghị", "đề xuất", "trình chính phủ", "trình quốc hội", # REPORTS_TO
    "phối hợp", "ký kết", "liên ngành",                                 # COORDINATES_WITH
    "thăm và làm việc", "thị sát", "kiểm tra thực địa",                 # WORKING_VISIT
    "huân chương", "bằng khen", "biểu dương", "khen thưởng",            # COMMENDS_AWARDS
    "bầu", "phê chuẩn miễn nhiệm", "trình hđnd",                        # LOCAL_ELECTIONS
    "khởi tố", "bắt giữ", "tạm giam", "truy tố", "xét xử",             # LEGAL_ACTIONS
    "thi hành kỷ luật", "xử lý kỷ luật", "khai trừ đảng",               # DISCIPLINE_PARTY
    "giao đất", "thu hồi đất", "đền bù giải phóng mặt bằng",            # LAND_MANAGEMENT
    "cấp phép", "thu hồi giấy phép", "đình chỉ",                        # PERMITS
]


# ==============================================================================
# 2. LỚP THU THẬP DỮ LIỆU BÁO MỚI (BAOMOI CRAWLER)
# ==============================================================================

class BaoMoiPoliticalCrawler:
    def __init__(self, output_file="baomoi_political_corpus.jsonl", visited_file="visited_urls.txt"):
        self.output_file = output_file
        self.visited_file = visited_file
        self.visited_urls = self._load_visited_urls()
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        })

    def _load_visited_urls(self) -> set:
        if os.path.exists(self.visited_file):
            with open(self.visited_file, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _mark_visited(self, url: str):
        self.visited_urls.add(url)
        with open(self.visited_file, "a", encoding="utf-8") as f:
            f.write(url + "\n")

    def get_article_links_from_page(self, page_url: str) -> list:
        """Lấy toàn bộ danh sách URL bài báo (có đuôi -cXXXX.epi) từ trang danh mục hoặc tìm kiếm"""
        links = set()
        try:
            resp = self.session.get(page_url, timeout=15)
            if resp.status_code != 200:
                return []
            
            soup = BeautifulSoup(resp.text, "lxml")
            
            # Cách 1: Quét các thẻ <a> có pattern bài viết chuẩn của Báo Mới: *-c<số_id>.epi
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].split("?")[0]
                if re.search(r"-c\d+\.epi$", href):
                    full_url = urljoin(BASE_URL, href)
                    links.add(full_url)

            # Cách 2: Bóc tách thêm từ __NEXT_DATA__ (vì Báo Mới dùng React render)
            next_data_script = soup.find("script", id="__NEXT_DATA__")
            if next_data_script and next_data_script.string:
                raw_json = next_data_script.string
                # Tìm mọi đường dẫn có dạng /...-c12345678.epi nằm trong JSON
                matches = re.findall(r'(/[a-zA-Z0-9\\-]+-c\d+\.epi)', raw_json)
                for m in matches:
                    links.add(urljoin(BASE_URL, m))

        except Exception as e:
            print(f"[!] Lỗi khi quét trang danh sách {page_url}: {e}")
            
        return list(links)

    def parse_article(self, article_url: str) -> dict:
        """Bóc tách Tiêu đề, Tóm tắt, Nội dung chi tiết, Báo gốc và Ngày đăng từ URL Báo Mới"""
        try:
            resp = self.session.get(article_url, timeout=15)
            if resp.status_code != 200:
                return None

            html = resp.text
            soup = BeautifulSoup(html, "lxml")

            title = ""
            description = ""
            body_paragraphs = []
            publisher = "Báo Mới"
            published_date = ""
            original_source_url = ""

            # --- TẦNG 1: Bóc tách từ JSON __NEXT_DATA__ của Báo Mới ---
            next_script = soup.find("script", id="__NEXT_DATA__")
            if next_script and next_script.string:
                try:
                    data = json.loads(next_script.string)
                    # Tìm đệ quy đối tượng chứa thông tin bài viết trong JSON tree
                    article_data = self._find_article_node_in_json(data)
                    if article_data:
                        title = article_data.get("title", "")
                        description = article_data.get("description", "")
                        published_date = str(article_data.get("date", ""))
                        original_source_url = article_data.get("originalUrl", "")
                        
                        if "publisher" in article_data and isinstance(article_data["publisher"], dict):
                            publisher = article_data["publisher"].get("name", publisher)
                            
                        # Lấy các đoạn văn trong trường body
                        for item in article_data.get("body", []):
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_val = BeautifulSoup(item.get("content", ""), "lxml").get_text(" ", strip=True)
                                if text_val:
                                    body_paragraphs.append(text_val)
                except Exception:
                    pass

            # --- TẦNG 2: Bóc tách từ HTML & Trafilatura nếu __NEXT_DATA__ đổi cấu trúc ---
            if not title:
                h1 = soup.find("h1")
                title = h1.get_text(strip=True) if h1 else ""

            if not description:
                meta_desc = soup.find("meta", attrs={"name": "description"})
                description = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""

            if len(body_paragraphs) < 2:
                # Dùng trafilatura rút trích văn bản sạch
                extracted_text = trafilatura.extract(html, include_comments=False, include_tables=False)
                if extracted_text:
                    body_paragraphs = [p.strip() for p in extracted_text.split("\n") if len(p.strip()) > 30]

            # --- TẦNG 3: Nếu Báo Mới chỉ đăng tóm tắt, tự động nhảy sang link Báo Gốc lấy Full-Text ---
            full_text = "\n".join(body_paragraphs)
            if len(full_text) < 250 and original_source_url.startswith("http"):
                downloaded = trafilatura.fetch_url(original_source_url)
                if downloaded:
                    orig_text = trafilatura.extract(downloaded, include_comments=False)
                    if orig_text and len(orig_text) > len(full_text):
                        full_text = orig_text

            if not title or len(full_text) < 150:
                return None

            return {
                "article_id": re.search(r"-c(\d+)\.epi", article_url).group(1) if re.search(r"-c(\d+)\.epi", article_url) else "",
                "baomoi_url": article_url,
                "original_url": original_source_url,
                "publisher": publisher,
                "published_date": published_date,
                "title": title,
                "sapo": description,
                "content": full_text
            }

        except Exception as e:
            return None

    def _find_article_node_in_json(self, obj):
        """Hàm đệ quy tìm nhánh JSON chứa thông tin chi tiết bài báo trong __NEXT_DATA__"""
        if isinstance(obj, dict):
            if "title" in obj and ("body" in obj or "description" in obj) and "id" in obj:
                return obj
            for k, v in obj.items():
                res = self._find_article_node_in_json(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_article_node_in_json(item)
                if res:
                    return res
        return None

    def is_relevant_political_news(self, article: dict) -> bool:
        """
        Kiểm tra bài báo có chứa cả Thực thể chính trị (Node) và Từ khóa hành động (Edge)
        để đảm bảo độ chính xác cao cho bước NLP phía sau.
        """
        combined_text = f"{article['title']} {article['sapo']} {article['content']}".lower()
        
        has_entity = any(kw in combined_text for kw in POLITICAL_ENTITY_KEYWORDS)
        has_relation = any(kw in combined_text for kw in RELATION_TRIGGER_KEYWORDS)
        
        return has_entity and has_relation

    def save_article(self, article: dict):
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(article, ensure_ascii=False) + "\n")

    def run(self, max_pages_per_cat=30, max_pages_per_query=15, max_pages_per_local=5):
        """
        Chạy crawler qua 3 bước:
        1. Quét theo chuyên mục Báo Mới
        2. Quét theo từ khóa cấp Trung ương
        3. Quét theo từ khóa cấp địa phương (tỉnh × sở/huyện/xã)
        
        Args:
            max_pages_per_cat: Số trang tối đa mỗi chuyên mục
            max_pages_per_query: Số trang tối đa mỗi từ khóa TW
            max_pages_per_local: Số trang tối đa mỗi từ khóa địa phương (ít hơn vì rất nhiều query)
        """
        total_saved = 0
        
        # ====== BƯỚC 1: Quét theo Chuyên mục (Thời sự, Chính trị, Xã hội) ======
        print("=" * 70)
        print("=== BƯỚC 1: QUÉT THEO CHUYÊN MỤC BÁO MỚI ===")
        print("=" * 70)
        for cat_path in CATEGORY_PATHS:
            for page in range(1, max_pages_per_cat + 1):
                page_url = f"{BASE_URL}{cat_path}" if page == 1 else f"{BASE_URL}{cat_path.replace('.epi', '')}/trang{page}.epi"
                links = self.get_article_links_from_page(page_url)
                new_links = [l for l in links if l not in self.visited_urls]
                
                if not new_links:
                    break
                    
                print(f"[*] Chuyên mục {cat_path} - Trang {page}: Tìm thấy {len(new_links)} bài mới.")
                for link in tqdm(new_links, desc=f"Crawling {cat_path} P{page}", leave=False):
                    self._mark_visited(link)
                    article = self.parse_article(link)
                    if article and self.is_relevant_political_news(article):
                        self.save_article(article)
                        total_saved += 1
                    time.sleep(random.uniform(0.4, 1.0))

        # ====== BƯỚC 2: Quét theo Từ khóa cấp Trung ương ======
        print("\n" + "=" * 70)
        print("=== BƯỚC 2: QUÉT THEO TỪ KHÓA CẤP TRUNG ƯƠNG ===")
        print("=" * 70)
        for query in SEARCH_QUERIES_CENTRAL:
            encoded_q = quote(query)
            for page in range(1, max_pages_per_query + 1):
                search_url = f"{BASE_URL}/tim-kiem/{encoded_q}.epi" if page == 1 else f"{BASE_URL}/tim-kiem/{encoded_q}/trang{page}.epi"
                links = self.get_article_links_from_page(search_url)
                new_links = [l for l in links if l not in self.visited_urls]
                
                if not new_links:
                    break
                    
                print(f"[*] TW '{query}' - Trang {page}: Tìm thấy {len(new_links)} bài mới.")
                for link in tqdm(new_links, desc=f"TW: {query[:20]}... P{page}", leave=False):
                    self._mark_visited(link)
                    article = self.parse_article(link)
                    if article and self.is_relevant_political_news(article):
                        self.save_article(article)
                        total_saved += 1
                    time.sleep(random.uniform(0.4, 1.0))

        # ====== BƯỚC 3: Quét theo Từ khóa cấp Địa phương (63 tỉnh × Sở/Huyện/Xã) ======
        print("\n" + "=" * 70)
        print(f"=== BƯỚC 3: QUÉT THEO TỪ KHÓA CẤP ĐỊA PHƯƠNG ({len(SEARCH_QUERIES_LOCAL)} từ khóa) ===")
        print("=" * 70)
        for i, query in enumerate(SEARCH_QUERIES_LOCAL, start=1):
            encoded_q = quote(query)
            for page in range(1, max_pages_per_local + 1):
                search_url = f"{BASE_URL}/tim-kiem/{encoded_q}.epi" if page == 1 else f"{BASE_URL}/tim-kiem/{encoded_q}/trang{page}.epi"
                links = self.get_article_links_from_page(search_url)
                new_links = [l for l in links if l not in self.visited_urls]
                
                if not new_links:
                    break
                    
                print(f"[*] ĐP [{i}/{len(SEARCH_QUERIES_LOCAL)}] '{query}' - Trang {page}: {len(new_links)} bài mới.")
                for link in tqdm(new_links, desc=f"ĐP: {query[:25]}... P{page}", leave=False):
                    self._mark_visited(link)
                    article = self.parse_article(link)
                    if article and self.is_relevant_political_news(article):
                        self.save_article(article)
                        total_saved += 1
                    time.sleep(random.uniform(0.4, 1.0))

            # In tiến độ tổng thể mỗi 50 query
            if i % 50 == 0:
                print(f"    >>> Đã quét {i}/{len(SEARCH_QUERIES_LOCAL)} từ khóa ĐP | Tổng bài đã lưu: {total_saved}")

        print(f"\n{'=' * 70}")
        print(f"[HOÀN TẤT] Đã thu thập và lọc thành công {total_saved} bài báo chất lượng cao.")
        print(f"  -> File output: '{self.output_file}'")
        print(f"  -> Tổng từ khóa đã quét: {len(SEARCH_QUERIES_CENTRAL)} TW + {len(SEARCH_QUERIES_LOCAL)} ĐP")
        print(f"{'=' * 70}")


if __name__ == "__main__":
    crawler = BaoMoiPoliticalCrawler(
        output_file="baomoi_political_corpus.jsonl",
        visited_file="visited_baomoi_urls.txt"
    )
    # Tùy chỉnh số trang cần quét:
    # - max_pages_per_cat: Số trang mỗi chuyên mục (Thời sự, Chính trị, Xã hội)
    # - max_pages_per_query: Số trang mỗi từ khóa cấp Trung ương
    # - max_pages_per_local: Số trang mỗi từ khóa cấp Địa phương (nên giữ nhỏ vì có hàng trăm query)
    crawler.run(max_pages_per_cat=50, max_pages_per_query=15, max_pages_per_local=5)
