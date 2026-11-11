# -*- coding: utf-8 -*-
"""
TẠO CÁC HÌNH VẼ ĐỒ THỊ KIẾN TRÚC CHUẨN BÁO CÁO KHOA HỌC
Sử dụng Pillow (PIL) để render các sơ đồ kiến trúc độ phân giải cao (2x DPI).
Thể hiện đầy đủ kỹ thuật, giải thuật và thư viện cho từng khối chức năng.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "report" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD_PATH = "C:/Windows/Fonts/segoeuib.ttf"


def get_font(size, bold=False):
    try:
        path = FONT_BOLD_PATH if bold else FONT_PATH
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def draw_rounded_rect(draw, box, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)


def draw_arrow_down(draw, x, y1, y2, color="#64748B", width=3):
    draw.line([(x, y1), (x, y2)], fill=color, width=width)
    draw.polygon([(x - 6, y2 - 8), (x + 6, y2 - 8), (x, y2 + 2)], fill=color)


def draw_arrow_right(draw, x1, x2, y, color="#64748B", width=3):
    draw.line([(x1, y), (x2, y)], fill=color, width=width)
    draw.polygon([(x2 - 8, y - 6), (x2 - 8, y + 6), (x2 + 2, y)], fill=color)


# ==============================================================================
# HÌNH 1: KIẾN TRÚC TỔNG THỂ HỆ THỐNG VIGOV-IE v2.0
# ==============================================================================
def create_figure_1():
    W, H = 1420, 1060
    img = Image.new("RGB", (W, H), "#F8FAFC")
    draw = ImageDraw.Draw(img)

    # 1. Header Banner
    draw_rounded_rect(draw, (40, 25, W - 40, 105), radius=12, fill="#0F172A", outline="#1E293B", width=2)
    f_title = get_font(24, bold=True)
    f_sub = get_font(14, bold=False)
    draw.text((W / 2, 48), "KIẾN TRÚC TỔNG THỂ HỆ THỐNG VIGOV-IE v2.0 VỚI THƯ VIỆN & GIẢI THUẬT TRIỂN KHAI", font=f_title, fill="#FFFFFF", anchor="mm")
    draw.text((W / 2, 82), "Vietnamese Governance Knowledge Graph Construction via Syntax-Guided N-ary Event Reification", font=f_sub, fill="#94A3B8", anchor="mm")

    layers = [
        {
            "name": "TẦNG 1: THU THẬP DỮ LIỆU ĐA NGUỒN (DATA INGESTION LAYER - WIKI ĐỊNH HƯỚNG CRAWL BÁO)",
            "y": 125, "h": 160, "color": "#F1F5F9", "border": "#CBD5E1",
            "boxes": [
                ("Wikipedia tiếng Việt (Cơ sở)", 
                 "[Thư viện & Kỹ thuật]: requests + MediaWiki API, Regex Infobox Parser\n"
                 "• Duyệt BFS cây thể loại: 3.134 trang chính khách & cơ quan\n"
                 "• Regex bóc Infobox (| key = val): 1.798 Lãnh đạo, 1.181 Cơ quan", 
                 "#FEFCE8", "#CA8A04"),
                ("Crawl Báo chí có Mục tiêu (Targeted)", 
                 "[Thư viện & Kỹ thuật]: feedparser + Google News RSS Query Generator\n"
                 "• Đọc 1.798 tên lãnh đạo từ Wiki sinh query RSS tự động:\n"
                 "  '\"[Tên Lãnh đạo]\" (bổ nhiệm OR chỉ đạo OR kỷ luật OR thanh tra...)'", 
                 "#EFF6FF", "#2563EB"),
                ("Crawl Báo chí theo Chuyên mục", 
                 "[Thư viện & Kỹ thuật]: BeautifulSoup4 + Requests, Hashlib MD5 URL Dedup\n"
                 "• 16.757 bài báo từ Báo Chính phủ, VnExpress, Báo Tin tức...\n"
                 "• Lọc theo chuyên mục Thời sự, Chính trị, Chỉ đạo & Quyết định", 
                 "#FFFFFF", "#3B82F6")
            ]
        },
        {
            "name": "TẦNG 2: TIỀN XỬ LÝ & LIÊN KẾT THỰC THỂ (TEXT PREPROCESSING & ENTITY LINKING)",
            "y": 315, "h": 165, "color": "#EFF6FF", "border": "#BFDBFE",
            "boxes": [
                ("Từ điển Thực thể Wiki (Gazetteer)", 
                 "[Thư viện & Cấu trúc]: Hash Table O(1) tra cứu trong bộ nhớ RAM\n"
                 "• 1.798 Người · 1.181 Cơ quan · 1.563 Chức vụ từ Infobox\n"
                 "• Đóng vai trò 'Khung neo' định danh duy nhất (Canonical IDs)", 
                 "#FEFCE8", "#CA8A04"),
                ("Tiền xử lý Ngữ liệu Báo chí", 
                 "[Thư viện & Kỹ thuật]: unicodedata (NFC) + Regex Lookbehind Splitter\n"
                 "• Chuẩn hóa Unicode NFC, thống nhất dấu thanh nguyên âm đôi\n"
                 "• Tách 442.314 câu bảo vệ chữ viết tắt chức danh: TP., PGS.TS., ThS.", 
                 "#FFFFFF", "#2563EB"),
                ("Nhận diện & Liên kết Thực thể (NER)", 
                 "[Thư viện & Kỹ thuật]: Aho-Corasick Longest Match + Canonical Slug\n"
                 "• Khớp tên báo chí vào Gazetteer Wiki → Gán ID Wiki chính tắc\n"
                 "• Mẫu ngữ cảnh chức vụ phát hiện lãnh đạo mới ngoài Wiki 'per:news:...'", 
                 "#FEF3C7", "#D97706")
            ]
        },
        {
            "name": "TẦNG 3: ĐỘNG CƠ TRÍCH XUẤT SỰ KIỆN N-NGÔI VIGOV-IE v2.0 (EVENT EXTRACTION ENGINE - 12.671 CÂU/GIÂY)",
            "y": 510, "h": 275, "color": "#F0FDF4", "border": "#BBF7D0",
            "boxes": [
                ("Phân loại Sự kiện (10 Loại)", 
                 "[Kỹ thuật]: Trigger Lexicon + Context Window (120 chars)\n"
                 "Bổ nhiệm, Kỷ luật, Chỉ đạo, Chủ trì, Làm việc, Miễn nhiệm...\n"
                 "Lọc âm tính/dương tính giả: Phủ định, từ đa nghĩa ngữ cảnh", 
                 "#FFFFFF", "#059669"),
                ("Bóc tách Văn bản & Thời hạn", 
                 "[Kỹ thuật]: Biểu thức chính quy Regex pháp lý đa mẫu\n"
                 "• legal_doc: Regex số quyết định '\\d+/[A-ZĐ0-9\\-_]+' (F1 99.4%)\n"
                 "• deadline: Regex mốc thời gian (F1 100%) · urgency: Lexicon (100%)", 
                 "#FFFFFF", "#059669"),
                ("Scoped Position Matcher", 
                 "[Kỹ thuật]: Trie Matching trên từ điển 1.563 Chức vụ Wiki\n"
                 "• role: Lookbehind sau 'giữ chức/làm' (F1 97.2%)\n"
                 "• appoint_type: Heuristic ưu tiên 13 động từ ghép (F1 100%)", 
                 "#FFFFFF", "#059669"),
                ("Multi-target Coordination", 
                 "[Kỹ thuật]: Token Delimiter Splitting (re.split) + 1-1 Alignment\n"
                 "• Phân rã danh sách kỷ luật nhiều đối tượng thành từng vế đơn\n"
                 "• penalty_form: Bảng 7 mức kỷ luật Đảng/CQ (F1 97.8%)", 
                 "#FFFFFF", "#059669"),
                ("Positional Entity Masking", 
                 "[Kỹ thuật]: Substring Masking (<AGENT>, <TARGET>) + Regex Strip\n"
                 "• Loại bỏ trợ từ, modal verbs, cơ quan nhận lệnh, trạng ngữ mở đầu\n"
                 "• action_content đạt 97.5% dùng được (so với 35% của underthesea)", 
                 "#FFFFFF", "#059669"),
                ("Discourse Buffer & Passive", 
                 "[Kỹ thuật]: Syntactic Passive Inversion Rule + Discourse Buffer\n"
                 "• Đảo chủ thể - đối tượng cho câu bị động ('ông A được bổ nhiệm')\n"
                 "• Bộ nhớ đệm liên câu giải quyết Zero Anaphora cho đại từ", 
                 "#FFFFFF", "#059669")
            ]
        },
        {
            "name": "TẦNG 4: KHỬ TRÙNG, HỢP NHẤT & LƯU TRỮ ĐỒ THỊ TRI THỨC (GRAPH STORAGE & ANALYTICS)",
            "y": 815, "h": 210, "color": "#FAF5FF", "border": "#E9D5FF",
            "boxes": [
                ("Thuật toán Partitioned Linkage v2", 
                 "[Kỹ thuật]: 3-Tuple Blocking Matrix (Kind, Prefix, Core) + Alias Dictionary\n"
                 "• Triệt tiêu 100% Cạm bẫy Trùng tiền tố: Đảng ≠ Chính quyền, Hà Nội ≠ Cần Thơ\n"
                 "• Kết quả trên 8.937 cạnh: Độ chính xác 100.0%, 0 false merge, 0.117 giây", 
                 "#FEF3C7", "#D97706"),
                ("Lược đồ Đồ thị N-ngôi (:Event)", 
                 "[Kỹ thuật]: Event Reification Pattern trên Neo4j Labeled Property Graph\n"
                 "• 8.581 Nodes (5.4K Person, 1.5K Org, 1.5K Position, 64 Province)\n"
                 "• 6.694 :Event Nodes lưu 9 tham số + 18.189 Quan hệ (19 loại)", 
                 "#FFFFFF", "#7C3AED"),
                ("Hệ quản trị & Phân tích Mạng", 
                 "[Thư viện]: Neo4j 5.26 Community + APOC 5.26 + Neo4j GDS 2.6+\n"
                 "• py2neo / neo4j-driver: Batch UNWIND load 5.000 dòng/batch\n"
                 "• Neo4j GDS: PageRank, WCC LCC (4.868 nodes), Sigma.js Visualizer", 
                 "#FFFFFF", "#7C3AED")
            ]
        }
    ]

    for layer in layers:
        ly = layer["y"]
        lh = layer["h"]
        draw_rounded_rect(draw, (40, ly, W - 40, ly + lh), radius=10, fill=layer["color"], outline=layer["border"], width=1)
        f_layer_hdr = get_font(13, bold=True)
        draw.text((60, ly + 14), layer["name"], font=f_layer_hdr, fill="#334155")
        
        boxes = layer["boxes"]
        n_box = len(boxes)
        box_y = ly + 36
        box_h = lh - 48
        gap = 16
        total_w = W - 120
        box_w = (total_w - (n_box - 1) * gap) / n_box if n_box <= 3 else (total_w - 2 * gap) / 3
        
        for i, b in enumerate(boxes):
            if n_box <= 3:
                bx = 60 + i * (box_w + gap)
                by = box_y
                bh = box_h
            else:
                row = i // 3
                col = i % 3
                bx = 60 + col * (box_w + gap)
                bh = (box_h - gap) / 2
                by = box_y + row * (bh + gap)
                
            draw_rounded_rect(draw, (bx, by, bx + box_w, by + bh), radius=8, fill=b[2], outline=b[3], width=1)
            draw.text((bx + 12, by + 8), b[0], font=get_font(12, bold=True), fill="#0F172A")
            lines = b[1].split("\n")
            line_y = by + 26
            for l in lines:
                is_kw = l.startswith("[") and "]" in l
                f_cur = get_font(10.5, bold=is_kw)
                c_cur = "#047857" if is_kw else "#475569"
                draw.text((bx + 12, line_y), l, font=f_cur, fill=c_cur)
                line_y += 16

    # Connecting arrows between layers
    draw_arrow_down(draw, W / 2, 285, 315, color="#64748B", width=3)
    draw_arrow_down(draw, W / 2, 480, 510, color="#64748B", width=3)
    draw_arrow_down(draw, W / 2, 785, 815, color="#64748B", width=3)

    img.save(FIG_DIR / "hinh1_kien_truc_tong_the.png", "PNG", dpi=(300, 300))
    print("✅ Đã tạo Hình 1: hinh1_kien_truc_tong_the.png (chuẩn kỹ thuật & thư viện)")


# ==============================================================================
# HÌNH 2: CƠ CHẾ KHỬ TRÙNG PHÂN RÃ ĐẶC TRƯNG (PARTITIONED RECORD LINKAGE)
# ==============================================================================
def create_figure_2():
    W, H = 1320, 800
    img = Image.new("RGB", (W, H), "#F8FAFC")
    draw = ImageDraw.Draw(img)

    # Header
    draw_rounded_rect(draw, (40, 25, W - 40, 100), radius=12, fill="#0F172A", outline="#1E293B", width=2)
    draw.text((W / 2, 48), "THUẬT TOÁN KHỬ TRÙNG THỰC THỂ PHÂN RÃ ĐẶC TRƯNG (PARTITIONED RECORD LINKAGE v2)", font=get_font(20, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((W / 2, 78), "Kỹ thuật Giải quyết triệt để Cạm bẫy Trùng tiền tố bằng Blocking Ma trận Thể chế cứng", font=get_font(13.5, bold=False), fill="#94A3B8", anchor="mm")

    # Column 1: Cạm bẫy Trùng tiền tố (Naive Fuzzy Matching)
    col1_x = 50
    col1_w = 370
    draw_rounded_rect(draw, (col1_x, 120, col1_x + col1_w, 750), radius=10, fill="#FEF2F2", outline="#FCA5A5", width=2)
    draw.text((col1_x + col1_w / 2, 145), "1. CẠM BẪY SO KHỚP MỜ CHUỖI", font=get_font(14.5, bold=True), fill="#991B1B", anchor="mm")
    draw.text((col1_x + col1_w / 2, 170), "[Thư viện đối chứng]: RapidFuzz / FuzzyWuzzy", font=get_font(11.5, bold=False), fill="#7F1D1D", anchor="mm")

    # Trap Example Box 1
    draw_rounded_rect(draw, (col1_x + 15, 195, col1_x + col1_w - 15, 310), radius=8, fill="#FFFFFF", outline="#F87171", width=1)
    draw.text((col1_x + 25, 205), "Thực thể A:", font=get_font(12, bold=True), fill="#0F172A")
    draw.text((col1_x + 25, 225), "'UBND Thành phố Hà Nội'", font=get_font(13, bold=True), fill="#1E40AF")
    draw.text((col1_x + 25, 250), "Thực thể B:", font=get_font(12, bold=True), fill="#0F172A")
    draw.text((col1_x + 25, 270), "'UBND Thành phố Cần Thơ'", font=get_font(13, bold=True), fill="#B91C1C")

    # Score calculation badge
    draw_rounded_rect(draw, (col1_x + 25, 330, col1_x + col1_w - 25, 435), radius=8, fill="#FEE2E2", outline="#EF4444", width=1)
    draw.text((col1_x + col1_w / 2, 350), "Thuật toán Token Set Ratio:", font=get_font(12, bold=True), fill="#991B1B", anchor="mm")
    draw.text((col1_x + col1_w / 2, 378), "Độ tương đồng: 90.4%", font=get_font(16, bold=True), fill="#DC2626", anchor="mm")
    draw.text((col1_x + col1_w / 2, 408), "Ngưỡng tiêu chuẩn: 85.0% → GỘP NHẦM", font=get_font(11, bold=True), fill="#7F1D1D", anchor="mm")

    # Error consequence
    draw_rounded_rect(draw, (col1_x + 15, 455, col1_x + col1_w - 15, 605), radius=8, fill="#FFFFFF", outline="#EF4444", width=1)
    draw.text((col1_x + 25, 470), "HẬU QUẢ TAI HẠI (OVER-MERGE):", font=get_font(12, bold=True), fill="#B91C1C")
    lines_c1 = [
        "❌ Hà Nội bị gộp chung với Cần Thơ",
        "❌ Bình Dương bị gộp chung với Bình Phước",
        "❌ Tỉnh ủy bị gộp với UBND (98/108 cặp)",
        "❌ Phá hủy 100% tính toàn vẹn của Đồ thị"
    ]
    cy = 500
    for l in lines_c1:
        draw.text((col1_x + 25, cy), l, font=get_font(11, bold=False), fill="#991B1B")
        cy += 24

    draw_rounded_rect(draw, (col1_x + 25, 635, col1_x + col1_w - 25, 715), radius=8, fill="#EF4444", outline="#B91C1C", width=1)
    draw.text((col1_x + col1_w / 2, 660), "KẾT QUẢ ĐỐI CHỨNG MỜ:", font=get_font(12, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((col1_x + col1_w / 2, 688), "Độ chính xác: 0.0% (Lỗi 100%)", font=get_font(14, bold=True), fill="#FFFFFF", anchor="mm")

    # Arrow 1 -> 2
    draw_arrow_right(draw, col1_x + col1_w + 5, col1_x + col1_w + 35, 430, color="#64748B", width=3)

    # Column 2: Phân rã 3 thành phần (Partitioned Decomposition)
    col2_x = 470
    col2_w = 410
    draw_rounded_rect(draw, (col2_x, 120, col2_x + col2_w, 750), radius=10, fill="#F0FDF4", outline="#86EFAC", width=2)
    draw.text((col2_x + col2_w / 2, 145), "2. PHÂN RÃ ĐẶC TRƯNG 3 THÀNH PHẦN", font=get_font(14.5, bold=True), fill="#166534", anchor="mm")
    draw.text((col2_x + col2_w / 2, 170), "[Giải thuật]: Entity Slug 3-Tuple Decomposition Rule", font=get_font(11.5, bold=False), fill="#14532D", anchor="mm")

    # Formula box
    draw_rounded_rect(draw, (col2_x + 15, 195, col2_x + col2_w - 15, 275), radius=8, fill="#DCFCE7", outline="#22C55E", width=1)
    draw.text((col2_x + col2_w / 2, 215), "Công thức phân rã bộ ba chính tắc:", font=get_font(12, bold=True), fill="#166534", anchor="mm")
    draw.text((col2_x + col2_w / 2, 245), "Entity Slug = (Kind, Prefix_Context, Core_Name)", font=get_font(13, bold=True), fill="#0F172A", anchor="mm")

    # Decomposition Details Box
    draw_rounded_rect(draw, (col2_x + 15, 290, col2_x + col2_w - 15, 500), radius=8, fill="#FFFFFF", outline="#86EFAC", width=1)
    draw.text((col2_x + 25, 303), "Cơ chế phân rã cơ quan (ORG):", font=get_font(12, bold=True), fill="#15803D")
    
    decomp_examples = [
        ("org:ubnd_tp_ha_noi", "kind='org' | prefix='ubnd_tp' | core='ha_noi'"),
        ("org:ubnd_tp_can_tho", "kind='org' | prefix='ubnd_tp' | core='can_tho'"),
        ("org:tinh_uy_dong_nai", "kind='org_party' | prefix='tinh_uy' | core='dong_nai'"),
        ("org:ubnd_tinh_dong_nai", "kind='org_gov' | prefix='ubnd' | core='dong_nai'")
    ]
    dy = 330
    for raw, dec in decomp_examples:
        draw.text((col2_x + 25, dy), raw, font=get_font(11, bold=True), fill="#1E293B")
        draw.text((col2_x + 25, dy + 18), "↳ " + dec, font=get_font(10.5, bold=False), fill="#059669")
        dy += 40

    # Person decomposition
    draw_rounded_rect(draw, (col2_x + 15, 515, col2_x + col2_w - 15, 715), radius=8, fill="#FFFFFF", outline="#86EFAC", width=1)
    draw.text((col2_x + 25, 528), "Cơ chế phân rã cá nhân (PER):", font=get_font(12, bold=True), fill="#15803D")
    draw.text((col2_x + 25, 555), "Tách [Họ tên cốt lõi] vs [Hậu tố địa danh/chức vụ]", font=get_font(11, bold=True), fill="#334155")
    draw.text((col2_x + 25, 580), "per:news:nguyen_thanh_hung_dong_thap", font=get_font(11, bold=True), fill="#1E293B")
    draw.text((col2_x + 25, 600), "↳ core_name = 'nguyen_thanh_hung' (Tên người)", font=get_font(10.5, bold=False), fill="#059669")
    draw.text((col2_x + 25, 620), "↳ ctx_part   = 'dong_thap' (Địa danh context)", font=get_font(10.5, bold=False), fill="#059669")
    draw.text((col2_x + 25, 650), "Chặn hoàn toàn gộp sai với 'nguyen_thanh_dieu'!", font=get_font(11, bold=True), fill="#15803D")

    # Arrow 2 -> 3
    draw_arrow_right(draw, col2_x + col2_w + 5, col2_x + col2_w + 35, 430, color="#64748B", width=3)

    # Column 3: Quyết định Khử trùng (Blocking & Decision)
    col3_x = 920
    col3_w = 360
    draw_rounded_rect(draw, (col3_x, 120, col3_x + col3_w, 750), radius=10, fill="#EFF6FF", outline="#93C5FD", width=2)
    draw.text((col3_x + col3_w / 2, 145), "3. QUYẾT ĐỊNH KHỬ TRÙNG ĐỒ THỊ", font=get_font(14.5, bold=True), fill="#1E40AF", anchor="mm")
    draw.text((col3_x + col3_w / 2, 170), "[Kỹ thuật]: Deterministic Hard Blocking Matrix", font=get_font(11.5, bold=False), fill="#1E3A8A", anchor="mm")

    # Match Rule 1: Institutional Blocking
    draw_rounded_rect(draw, (col3_x + 15, 195, col3_x + col3_w - 15, 345), radius=8, fill="#FFFFFF", outline="#3B82F6", width=1)
    draw.text((col3_x + 25, 208), "Quy tắc 1: Chặn Thể chế cứng", font=get_font(12, bold=True), fill="#1D4ED8")
    draw.text((col3_x + 25, 230), "Kind(Đảng) ≠ Kind(Chính quyền)", font=get_font(12, bold=True), fill="#DC2626")
    draw.text((col3_x + 25, 255), "Cơ chế: Hard Institutional Blocking Matrix", font=get_font(10.5, bold=False), fill="#475569")
    draw.text((col3_x + 25, 278), "Quyết định: TUYỆT ĐỐI KHÔNG GỘP", font=get_font(12, bold=True), fill="#16A34A")
    draw.text((col3_x + 25, 305), "✅ Triệt tiêu 100% bẫy Tỉnh ủy vs UBND", font=get_font(11, bold=True), fill="#15803D")

    # Match Rule 2: Same Core + Alias -> Merge
    draw_rounded_rect(draw, (col3_x + 15, 360, col3_x + col3_w - 15, 510), radius=8, fill="#FFFFFF", outline="#3B82F6", width=1)
    draw.text((col3_x + 25, 373), "Quy tắc 2: Ánh xạ Từ điển Bí danh", font=get_font(12, bold=True), fill="#1D4ED8")
    draw.text((col3_x + 25, 395), "config/org_aliases.json Lookup Table", font=get_font(11, bold=True), fill="#059669")
    draw.text((col3_x + 25, 420), "Core('tp_hcm') → Core('tp_ho_chi_minh')", font=get_font(10.5, bold=False), fill="#475569")
    draw.text((col3_x + 25, 442), "Quyết định: HỢP NHẤT AN TOÀN", font=get_font(12, bold=True), fill="#2563EB")
    draw.text((col3_x + 25, 470), "✅ Chuẩn hóa viết tắt Sở KH&ĐT, TP.HCM", font=get_font(11, bold=True), fill="#15803D")

    # Performance Banner
    draw_rounded_rect(draw, (col3_x + 15, 530, col3_x + col3_w - 15, 715), radius=8, fill="#1E293B", outline="#0F172A", width=1)
    draw.text((col3_x + col3_w / 2, 555), "HIỆU NĂNG THỰC TẾ TRÊN 8.937 CẠNH:", font=get_font(11.5, bold=True), fill="#FBBF24", anchor="mm")
    
    perf_lines = [
        "• Độ chính xác Khử trùng: 100.0%",
        "• Số cạnh trước khử trùng: 8.937",
        "• Số cạnh sau gộp an toàn: 4.583",
        "• Thời gian xử lý: 0.117 giây",
        "• Tốc độ: 76.384 cạnh / giây"
    ]
    py = 585
    for l in perf_lines:
        draw.text((col3_x + 30, py), l, font=get_font(11.5, bold=False), fill="#FFFFFF")
        py += 24

    img.save(FIG_DIR / "hinh2_partitioned_record_linkage.png", "PNG", dpi=(300, 300))
    print("✅ Đã tạo Hình 2: hinh2_partitioned_record_linkage.png (chuẩn kỹ thuật & thư viện)")


# ==============================================================================
# HÌNH 3: KHUNG NGỮ NGHĨA SỰ KIỆN N-NGÔI (EVENT REIFICATION)
# ==============================================================================
def create_figure_3():
    W, H = 1320, 860
    img = Image.new("RGB", (W, H), "#F8FAFC")
    draw = ImageDraw.Draw(img)

    # Header
    draw_rounded_rect(draw, (40, 25, W - 40, 100), radius=12, fill="#0F172A", outline="#1E293B", width=2)
    draw.text((W / 2, 48), "MÔ HÌNH HÓA SỰ KIỆN N-NGÔI (:EVENT REIFICATION) & KHUNG 9 THAM SỐ CHUYÊN SÂU", font=get_font(20, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((W / 2, 78), "[Công nghệ triển khai]: Neo4j Cypher 5.26 Property Graph · APOC · Batch UNWIND py2neo Load", font=get_font(13.5, bold=False), fill="#94A3B8", anchor="mm")

    # Center Event Node
    cx, cy = W / 2, 470
    draw_rounded_rect(draw, (cx - 160, cy - 70, cx + 160, cy + 70), radius=16, fill="#0284C7", outline="#0369A1", width=3)
    draw.text((cx, cy - 25), "NÚT SỰ KIỆN TRUNG TÂM", font=get_font(13, bold=True), fill="#BAE6FD", anchor="mm")
    draw.text((cx, cy + 2), ":Event (Reified Node)", font=get_font(20, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((cx, cy + 30), "event_type: BO_NHIEM | CHI_DAO | KY_LUAT...", font=get_font(11, bold=False), fill="#E0F2FE", anchor="mm")

    # Entity Nodes: Subject (Agent) on Left, Object (Target) on Right
    ax, ay = 180, cy
    draw_rounded_rect(draw, (ax - 130, ay - 60, ax + 130, ay + 60), radius=12, fill="#1E293B", outline="#0F172A", width=2)
    draw.text((ax, ay - 20), "CHỦ THỂ QUYẾT ĐỊNH", font=get_font(12, bold=True), fill="#94A3B8", anchor="mm")
    draw.text((ax, ay + 6), ":Organization / :Person", font=get_font(16, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((ax, ay + 30), "(Thủ tướng, Ban Bí thư, Tỉnh ủy)", font=get_font(11, bold=False), fill="#CBD5E1", anchor="mm")

    tx, ty = W - 180, cy
    draw_rounded_rect(draw, (tx - 130, ty - 60, tx + 130, ty + 60), radius=12, fill="#1E293B", outline="#0F172A", width=2)
    draw.text((tx, ty - 20), "ĐỐI TƯỢNG TÁC ĐỘNG", font=get_font(12, bold=True), fill="#94A3B8", anchor="mm")
    draw.text((tx, ty + 6), ":Person / :Organization", font=get_font(16, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((tx, ty + 30), "(Cán bộ bổ nhiệm, Bộ ngành chỉ đạo)", font=get_font(11, bold=False), fill="#CBD5E1", anchor="mm")

    # Connectors Agent -> Event -> Target
    draw.line([(ax + 130, ay), (cx - 160, cy)], fill="#0284C7", width=4)
    draw.polygon([(cx - 165, cy - 8), (cx - 165, cy + 8), (cx - 150, cy)], fill="#0284C7")
    draw.text(((ax + 130 + cx - 160) / 2, cy - 16), ":ISSUED_BY", font=get_font(12, bold=True), fill="#0284C7", anchor="mm")

    draw.line([(cx + 160, cy), (tx - 130, ty)], fill="#0284C7", width=4)
    draw.polygon([(tx - 135, ty - 8), (tx - 135, ty + 8), (tx - 120, ty)], fill="#0284C7")
    draw.text(((cx + 160 + tx - 130) / 2, cy - 16), ":TARGETS", font=get_font(12, bold=True), fill="#0284C7", anchor="mm")

    # 9 Specialized Arguments (surrounding cards)
    args_info = [
        # Top Row (3 items)
        ("1. legal_doc (Số hiệu văn bản)", 
         "[Kỹ thuật]: Regex số QĐ '\\d+/[A-ZĐ0-9\\-_]+'\nF1 = 99.4% (VD: 'Quyết định 397/QĐ-TTg')", 
         cx - 450, 150, 280, 85),
        ("2. appoint_type (Hình thức nhân sự)", 
         "[Kỹ thuật]: Heuristic ưu tiên 13 động từ ghép\nF1 = 100.0% ('Điều động và bổ nhiệm')", 
         cx - 140, 150, 280, 85),
        ("3. role (Chức vụ bổ nhiệm)", 
         "[Kỹ thuật]: Lookbehind + Trie 1.563 Chức vụ\nF1 = 97.2% ('Thứ trưởng Bộ Dân tộc')", 
         cx + 170, 150, 280, 85),
        
        # Bottom Row (3 items)
        ("4. penalty_form (Hình thức kỷ luật)", 
         "[Kỹ thuật]: Đối chiếu 7 mức kỷ luật Đảng/CQ\nF1 = 97.8% ('Cảnh cáo', 'Khai trừ')", 
         cx - 450, 680, 280, 85),
        ("5. violation_reason (Căn cứ kỷ luật)", 
         "[Kỹ thuật]: Regex bóc sau 'do/vì/vi phạm'\nNgắt ranh giới dấu chấm câu", 
         cx - 140, 680, 280, 85),
        ("6. action_content (Nội dung chỉ đạo)", 
         "[Kỹ thuật]: Positional Masking & Regex Strip\nĐạt 97.5% dùng được (0 crash, 12.6K câu/s)", 
         cx + 170, 680, 280, 85),

        # Side Middle Items
        ("7. deadline (Thời hạn)", 
         "[Kỹ thuật]: Regex mốc thời gian (F1 100%)\nVD: 'Trước ngày 30/6/2025'", 
         50, 260, 260, 75),
        ("8. urgency (Mức độ khẩn)", 
         "[Kỹ thuật]: Tra cứu Lexicon (F1 100%)\nVD: 'Hỏa tốc', 'Thượng khẩn'", 
         50, 680, 260, 75),
        ("9. evidence (Bằng chứng câu)", 
         "[Kỹ thuật]: Regex tách câu + MD5 Hash URL\nTrích dẫn nguyên văn câu gốc từ báo chí", 
         W - 310, 260, 260, 75)
    ]

    for title, desc, bx, by, bw, bh in args_info:
        draw_rounded_rect(draw, (bx, by, bx + bw, by + bh), radius=8, fill="#FFFFFF", outline="#0284C7", width=1)
        draw.text((bx + 10, by + 8), title, font=get_font(11.5, bold=True), fill="#0F172A")
        lines = desc.split("\n")
        ly = by + 28
        for l in lines:
            is_tech = l.startswith("[") and "]" in l
            draw.text((bx + 10, ly), l, font=get_font(10, bold=is_tech), fill="#059669" if is_tech else "#475569")
            ly += 16

    # Bottom Query Sample
    draw_rounded_rect(draw, (40, 790, W - 40, 840), radius=8, fill="#1E293B", outline="#0F172A", width=1)
    q_text = "Truy vấn Cypher: MATCH (a)-[:ISSUED_BY]->(e:Event {event_type:'BO_NHIEM'})-[:TARGETS]->(b) RETURN a.name, e.role, e.legal_doc, b.name"
    draw.text((W / 2, 815), q_text, font=get_font(11.5, bold=True), fill="#38BDF8", anchor="mm")

    img.save(FIG_DIR / "hinh3_khung_su_kien_n_ngoi.png", "PNG", dpi=(300, 300))
    print("✅ Đã tạo Hình 3: hinh3_khung_su_kien_n_ngoi.png (chuẩn kỹ thuật & thư viện)")


if __name__ == "__main__":
    create_figure_1()
    create_figure_2()
    create_figure_3()
