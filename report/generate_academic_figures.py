# -*- coding: utf-8 -*-
"""
TẠO CÁC HÌNH VẼ ĐỒ THỊ KIẾN TRÚC CHUẨN BÁO CÁO KHOA HỌC
Sử dụng Pillow (PIL) để render các sơ đồ kiến trúc độ phân giải cao (2x DPI).
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
    # Đầu mũi tên
    draw.polygon([(x - 6, y2 - 8), (x + 6, y2 - 8), (x, y2 + 2)], fill=color)

def draw_arrow_right(draw, x1, x2, y, color="#64748B", width=3):
    draw.line([(x1, y), (x2, y)], fill=color, width=width)
    draw.polygon([(x2 - 8, y - 6), (x2 - 8, y + 6), (x2 + 2, y)], fill=color)

# ==============================================================================
# HÌNH 1: KIẾN TRÚC TỔNG THỂ HỆ THỐNG VIGOV-IE
# ==============================================================================
def create_figure_1():
    W, H = 1400, 960
    img = Image.new("RGB", (W, H), "#F8FAFC")
    draw = ImageDraw.Draw(img)

    # 1. Header Banner
    draw_rounded_rect(draw, (40, 25, W - 40, 105), radius=12, fill="#0F172A", outline="#1E293B", width=2)
    f_title = get_font(26, bold=True)
    f_sub = get_font(15, bold=False)
    draw.text((W / 2, 48), "KIẾN TRÚC TỔNG THỂ HỆ THỐNG VIGOV-IE v2.0", font=f_title, fill="#FFFFFF", anchor="mm")
    draw.text((W / 2, 82), "Vietnamese Governance Information & Event Extraction with Syntax-Guided Reification", font=f_sub, fill="#94A3B8", anchor="mm")

    layers = [
        {
            "name": "TẦNG 1: THU THẬP DỮ LIỆU ĐA NGUỒN (DATA INGESTION LAYER)",
            "y": 125, "h": 140, "color": "#F1F5F9", "border": "#CBD5E1",
            "boxes": [
                ("Kho Wikipedia Tiếng Việt", "3.1K trang chính trị gia, cơ quan, tỉnh thành\nBóc tách Infobox, Seed Categories & BFS", "#FFFFFF", "#3B82F6"),
                ("Kho Báo chí Thời sự - Nội chính", "16.7K bài báo từ Báo Chính phủ, Nhân Dân, v.v.\nThu thập theo dòng sự kiện & chuyên mục", "#FFFFFF", "#3B82F6"),
                ("Dữ liệu Lãnh đạo & Tổ chức Chuẩn", "5.4K Politician Slugs & 1.8K Public Agencies\nDanh mục 63 tỉnh thành & 1.563 chức vụ", "#FFFFFF", "#3B82F6")
            ]
        },
        {
            "name": "TẦNG 2: TIỀN XỬ LÝ & KHỬ TRÙNG PHÂN RÃ (PARTITIONED RECORD LINKAGE)",
            "y": 295, "h": 150, "color": "#EFF6FF", "border": "#BFDBFE",
            "boxes": [
                ("Phân tách Câu & Chuẩn hóa NFC", "Làm sạch ký tự điều khiển, chấm câu hành chính\nNgắt câu logic bảo toàn số hiệu văn bản", "#FFFFFF", "#2563EB"),
                ("Nhận diện Thực thể Chính trị (NER)", "Trích xuất Thực thể: PER, ORG, LOC\nPhát hiện từ khóa kích hoạt sự kiện (Trigger)", "#FFFFFF", "#2563EB"),
                ("Thuật toán Partitioned Linkage", "Phân rã Slug: [Kind] + [Prefix] + [Core_Name]\nTriệt tiêu 100% Cạm bẫy Trùng tiền tố", "#FEF3C7", "#D97706")
            ]
        },
        {
            "name": "TẦNG 3: ĐỘNG CƠ TRÍCH XUẤT SỰ KIỆN N-NGÔI VIGOV-IE v2.0 (EVENT EXTRACTION ENGINE)",
            "y": 475, "h": 240, "color": "#F0FDF4", "border": "#BBF7D0",
            "boxes": [
                ("Phân loại Sự kiện (10 Loại)", "Bổ nhiệm, Kỷ luật, Chỉ đạo, Chủ trì,\nPhối hợp, Làm việc, Miễn nhiệm...", "#FFFFFF", "#059669"),
                ("Bóc tách Văn bản & Thời hạn", "Biểu thức chính quy Pháp lý nâng cao:\nlegal_doc (F1 99.4%), deadline (F1 100%)", "#FFFFFF", "#059669"),
                ("Scoped Position Matcher", "Đối sánh từ điển 1.563 chức vụ:\nrole (F1 97.2%), appoint_type (F1 100%)", "#FFFFFF", "#059669"),
                ("Multi-target Coordination", "Phân rã danh sách kỷ luật đa đối tượng:\nGhép cặp 1-1 (Target - Penalty_form)", "#FFFFFF", "#059669"),
                ("Positional Entity Masking", "Che Agent/Target để bóc action_content:\nBảo toàn mệnh đề mục đích 'nhằm / để'", "#FFFFFF", "#059669"),
                ("Discourse Buffer & Passive", "Bắt cầu ngữ cảnh liên câu (Zero Anaphora)\nPhân định Cơ quan đề nghị vs Quyết định", "#FFFFFF", "#059669")
            ]
        },
        {
            "name": "TẦNG 4: LƯU TRỮ & BIỂU DIỄN ĐỒ THỊ TRI THỨC (KNOWLEDGE GRAPH & STORAGE)",
            "y": 745, "h": 180, "color": "#FAF5FF", "border": "#E9D5FF",
            "boxes": [
                ("Đồ thị Thực thể Đa tầng (Nodes)", "5.4K :Person | 1.8K :Organization\n1.5K :Position | 63 :Province | 6.7K :Event", "#FFFFFF", "#7C3AED"),
                ("Quan hệ Đồ thị 19 Loại & 9 Tham số", "Edge Reification: Cạnh chứa đầy đủ tham số\n(action_content, role, deadline, urgency...)", "#FFFFFF", "#7C3AED"),
                ("Kho Lưu trữ Kết hợp (Hybrid Storage)", "DuckDB / Parquet Analytics: 12.671 câu/s\nNeo4j Property Graph cho trực quan hóa mạng lưới", "#FFFFFF", "#7C3AED")
            ]
        }
    ]

    for layer in layers:
        ly = layer["y"]
        lh = layer["h"]
        # Background layer card
        draw_rounded_rect(draw, (40, ly, W - 40, ly + lh), radius=10, fill=layer["color"], outline=layer["border"], width=1)
        # Layer header label
        f_layer_hdr = get_font(13, bold=True)
        draw.text((60, ly + 14), layer["name"], font=f_layer_hdr, fill="#334155")
        
        # Sub-boxes inside layer
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
            # Box Title
            draw.text((bx + 12, by + 10), b[0], font=get_font(13, bold=True), fill="#0F172A")
            # Box text lines
            lines = b[1].split("\n")
            line_y = by + 30
            for l in lines:
                draw.text((bx + 12, line_y), l, font=get_font(11, bold=False), fill="#475569")
                line_y += 18

    # Connecting arrows between layers
    draw_arrow_down(draw, W / 2, 265, 295, color="#64748B", width=3)
    draw_arrow_down(draw, W / 2, 445, 475, color="#64748B", width=3)
    draw_arrow_down(draw, W / 2, 715, 745, color="#64748B", width=3)

    img.save(FIG_DIR / "hinh1_kien_truc_tong_the.png", "PNG", dpi=(300, 300))
    print("✅ Đã tạo Hình 1: hinh1_kien_truc_tong_the.png")

# ==============================================================================
# HÌNH 2: CƠ CHẾ KHỬ TRÙNG PHÂN RÃ ĐẶC TRƯNG (PARTITIONED RECORD LINKAGE)
# ==============================================================================
def create_figure_2():
    W, H = 1300, 780
    img = Image.new("RGB", (W, H), "#F8FAFC")
    draw = ImageDraw.Draw(img)

    # Header
    draw_rounded_rect(draw, (40, 25, W - 40, 100), radius=12, fill="#0F172A", outline="#1E293B", width=2)
    draw.text((W / 2, 48), "THUẬT TOÁN KHỬ TRÙNG THỰC THỂ PHÂN RÃ ĐẶC TRƯNG (PARTITIONED RECORD LINKAGE)", font=get_font(21, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((W / 2, 78), "Giải quyết triệt để Cạm bẫy Trùng tiền tố (Common-prefix Trap) trong tiếng Việt hành chính", font=get_font(14, bold=False), fill="#94A3B8", anchor="mm")

    # Column 1: Cạm bẫy Trùng tiền tố (Naive Fuzzy Matching)
    col1_x = 50
    col1_w = 360
    draw_rounded_rect(draw, (col1_x, 120, col1_x + col1_w, 730), radius=10, fill="#FEF2F2", outline="#FCA5A5", width=2)
    draw.text((col1_x + col1_w / 2, 145), "1. CẠM BẪY TRÙNG TIỀN TỐ", font=get_font(15, bold=True), fill="#991B1B", anchor="mm")
    draw.text((col1_x + col1_w / 2, 170), "(Naive String Fuzzy Matching)", font=get_font(12, bold=False), fill="#7F1D1D", anchor="mm")

    # Trap Example Box 1
    draw_rounded_rect(draw, (col1_x + 15, 195, col1_x + col1_w - 15, 310), radius=8, fill="#FFFFFF", outline="#F87171", width=1)
    draw.text((col1_x + 25, 205), "Thực thể A:", font=get_font(12, bold=True), fill="#0F172A")
    draw.text((col1_x + 25, 225), "'UBND Thành phố Hà Nội'", font=get_font(13, bold=True), fill="#1E40AF")
    draw.text((col1_x + 25, 250), "Thực thể B:", font=get_font(12, bold=True), fill="#0F172A")
    draw.text((col1_x + 25, 270), "'UBND Thành phố Cần Thơ'", font=get_font(13, bold=True), fill="#B91C1C")

    # Score calculation badge
    draw_rounded_rect(draw, (col1_x + 25, 330, col1_x + col1_w - 25, 430), radius=8, fill="#FEE2E2", outline="#EF4444", width=1)
    draw.text((col1_x + col1_w / 2, 350), "Đo lường Token Set Ratio:", font=get_font(12, bold=True), fill="#991B1B", anchor="mm")
    draw.text((col1_x + col1_w / 2, 378), "Độ tương đồng: 90.4%", font=get_font(16, bold=True), fill="#DC2626", anchor="mm")
    draw.text((col1_x + col1_w / 2, 408), "Ngưỡng thường dùng: 85.0%", font=get_font(11, bold=False), fill="#7F1D1D", anchor="mm")

    # Error consequence
    draw_rounded_rect(draw, (col1_x + 15, 450, col1_x + col1_w - 15, 590), radius=8, fill="#FFFFFF", outline="#EF4444", width=1)
    draw.text((col1_x + 25, 465), "HẬU QUẢ TAI HẠI (OVER-MERGE):", font=get_font(12, bold=True), fill="#B91C1C")
    lines_c1 = [
        "❌ Hà Nội bị gộp chung với Cần Thơ",
        "❌ Bình Dương bị gộp chung với Bình Phước",
        "❌ Nguyễn Thanh Hùng bị gộp với N. T. Diệu",
        "❌ Phá hủy tính toàn vẹn của Đồ thị"
    ]
    cy = 495
    for l in lines_c1:
        draw.text((col1_x + 25, cy), l, font=get_font(11, bold=False), fill="#991B1B")
        cy += 22

    draw_rounded_rect(draw, (col1_x + 25, 620, col1_x + col1_w - 25, 700), radius=8, fill="#EF4444", outline="#B91C1C", width=1)
    draw.text((col1_x + col1_w / 2, 645), "KẾT QUẢ ĐỐI CHỨNG:", font=get_font(12, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((col1_x + col1_w / 2, 675), "Độ chính xác: 0.0% (Lỗi 100%)", font=get_font(14, bold=True), fill="#FFFFFF", anchor="mm")

    # Arrow 1 -> 2
    draw_arrow_right(draw, col1_x + col1_w + 5, col1_x + col1_w + 35, 420, color="#64748B", width=3)

    # Column 2: Phân rã 3 thành phần (Partitioned Decomposition)
    col2_x = 460
    col2_w = 400
    draw_rounded_rect(draw, (col2_x, 120, col2_x + col2_w, 730), radius=10, fill="#F0FDF4", outline="#86EFAC", width=2)
    draw.text((col2_x + col2_w / 2, 145), "2. PHÂN RÃ ĐẶC TRƯNG 3 THÀNH PHẦN", font=get_font(15, bold=True), fill="#166534", anchor="mm")
    draw.text((col2_x + col2_w / 2, 170), "(Entity Slug Decomposition Rule)", font=get_font(12, bold=False), fill="#14532D", anchor="mm")

    # Formula box
    draw_rounded_rect(draw, (col2_x + 15, 195, col2_x + col2_w - 15, 270), radius=8, fill="#DCFCE7", outline="#22C55E", width=1)
    draw.text((col2_x + col2_w / 2, 215), "Công thức phân rã:", font=get_font(12, bold=True), fill="#166534", anchor="mm")
    draw.text((col2_x + col2_w / 2, 245), "Entity Slug = (Kind, Prefix_Context, Core_Name)", font=get_font(13, bold=True), fill="#0F172A", anchor="mm")

    # Decomposition Details Box
    draw_rounded_rect(draw, (col2_x + 15, 285, col2_x + col2_w - 15, 490), radius=8, fill="#FFFFFF", outline="#86EFAC", width=1)
    draw.text((col2_x + 25, 298), "Cơ chế phân rã cơ quan (ORG):", font=get_font(12, bold=True), fill="#15803D")
    
    decomp_examples = [
        ("org:ubnd_tp_ha_noi", "kind='org' | prefix='ubnd_tp' | core='ha_noi'"),
        ("org:ubnd_tp_can_tho", "kind='org' | prefix='ubnd_tp' | core='can_tho'"),
        ("org:ubnd_tp_hcm", "kind='org' | prefix='ubnd_tp' | core='ho_chi_minh'"),
        ("org:so_gd_dt_phu_tho", "kind='org' | prefix='so_gd_dt' | core='phu_tho'")
    ]
    dy = 325
    for raw, dec in decomp_examples:
        draw.text((col2_x + 25, dy), raw, font=get_font(11, bold=True), fill="#1E293B")
        draw.text((col2_x + 25, dy + 18), "↳ " + dec, font=get_font(11, bold=False), fill="#059669")
        dy += 40

    # Person decomposition
    draw_rounded_rect(draw, (col2_x + 15, 505, col2_x + col2_w - 15, 700), radius=8, fill="#FFFFFF", outline="#86EFAC", width=1)
    draw.text((col2_x + 25, 518), "Cơ chế phân rã cá nhân (PER):", font=get_font(12, bold=True), fill="#15803D")
    draw.text((col2_x + 25, 545), "Tách [Họ tên cốt lõi] vs [Hậu tố địa danh]", font=get_font(11, bold=True), fill="#334155")
    draw.text((col2_x + 25, 570), "per:news:nguyen_thanh_hung_dong_thap", font=get_font(11, bold=True), fill="#1E293B")
    draw.text((col2_x + 25, 590), "↳ core_name = 'nguyen_thanh_hung' (Tên người)", font=get_font(11, bold=False), fill="#059669")
    draw.text((col2_x + 25, 610), "↳ ctx_part   = 'dong_thap' (Địa danh context)", font=get_font(11, bold=False), fill="#059669")
    draw.text((col2_x + 25, 638), "Khác biệt hoàn toàn với: 'nguyen_thanh_dieu'!", font=get_font(11, bold=True), fill="#DC2626")

    # Arrow 2 -> 3
    draw_arrow_right(draw, col2_x + col2_w + 5, col2_x + col2_w + 35, 420, color="#64748B", width=3)

    # Column 3: Quyết định Khử trùng (Blocking & Decision)
    col3_x = 890
    col3_w = 360
    draw_rounded_rect(draw, (col3_x, 120, col3_x + col3_w, 730), radius=10, fill="#EFF6FF", outline="#93C5FD", width=2)
    draw.text((col3_x + col3_w / 2, 145), "3. QUYẾT ĐỊNH KHỬ TRÙNG ĐỒ THỊ", font=get_font(15, bold=True), fill="#1E40AF", anchor="mm")
    draw.text((col3_x + col3_w / 2, 170), "(Strict Partitioned Blocking Decision)", font=get_font(12, bold=False), fill="#1E3A8A", anchor="mm")

    # Match Rule 1: Distinct Core -> Separate
    draw_rounded_rect(draw, (col3_x + 15, 195, col3_x + col3_w - 15, 340), radius=8, fill="#FFFFFF", outline="#3B82F6", width=1)
    draw.text((col3_x + 25, 208), "Trường hợp 1: Khác Core Name", font=get_font(12, bold=True), fill="#1D4ED8")
    draw.text((col3_x + 25, 230), "Core(ha_noi) != Core(can_tho)", font=get_font(12, bold=True), fill="#DC2626")
    draw.text((col3_x + 25, 255), "Cơ chế: Chặn phân vùng (Hard Blocking)", font=get_font(11, bold=False), fill="#475569")
    draw.text((col3_x + 25, 278), "Quyết định: GIỮ NGUYÊN TÁCH BIỆT", font=get_font(12, bold=True), fill="#16A34A")
    draw.text((col3_x + 25, 305), "✅ Triệt tiêu 100% lỗi gộp sai tỉnh thành", font=get_font(11, bold=True), fill="#15803D")

    # Match Rule 2: Same Core + Alias -> Merge
    draw_rounded_rect(draw, (col3_x + 15, 355, col3_x + col3_w - 15, 500), radius=8, fill="#FFFFFF", outline="#3B82F6", width=1)
    draw.text((col3_x + 25, 368), "Trường hợp 2: Trùng Core Name", font=get_font(12, bold=True), fill="#1D4ED8")
    draw.text((col3_x + 25, 390), "Core('tp_hcm') == Core('tp_ho_chi_minh')", font=get_font(11, bold=True), fill="#059669")
    draw.text((col3_x + 25, 415), "Cơ chế: Alias Canonicalization Lookup", font=get_font(11, bold=False), fill="#475569")
    draw.text((col3_x + 25, 438), "Quyết định: HỢP NHẤT AN TOÀN", font=get_font(12, bold=True), fill="#2563EB")
    draw.text((col3_x + 25, 465), "✅ Chuẩn hóa danh xưng viết tắt", font=get_font(11, bold=True), fill="#15803D")

    # Performance Banner
    draw_rounded_rect(draw, (col3_x + 15, 520, col3_x + col3_w - 15, 700), radius=8, fill="#1E293B", outline="#0F172A", width=1)
    draw.text((col3_x + col3_w / 2, 545), "HIỆU NĂNG THỰC TẾ TRÊN 8.937 CẠNH:", font=get_font(12, bold=True), fill="#FBBF24", anchor="mm")
    
    perf_lines = [
        "• Độ chính xác Khử trùng: 100.0%",
        "• Số cạnh trước khử trùng: 8.937",
        "• Số cạnh hợp nhất an toàn: 4.583",
        "• Thời gian xử lý: 0.117 giây",
        "• Tốc độ: 76.384 cạnh / giây"
    ]
    py = 575
    for l in perf_lines:
        draw.text((col3_x + 30, py), l, font=get_font(12, bold=False), fill="#FFFFFF")
        py += 24

    img.save(FIG_DIR / "hinh2_partitioned_record_linkage.png", "PNG", dpi=(300, 300))
    print("✅ Đã tạo Hình 2: hinh2_partitioned_record_linkage.png")

# ==============================================================================
# HÌNH 3: KHUNG NGỮ NGHĨA SỰ KIỆN N-NGÔI (EVENT REIFICATION)
# ==============================================================================
def create_figure_3():
    W, H = 1300, 840
    img = Image.new("RGB", (W, H), "#F8FAFC")
    draw = ImageDraw.Draw(img)

    # Header
    draw_rounded_rect(draw, (40, 25, W - 40, 100), radius=12, fill="#0F172A", outline="#1E293B", width=2)
    draw.text((W / 2, 48), "MÔ HÌNH HÓA SỰ KIỆN N-NGÔI (:EVENT REIFICATION) & KHUNG 9 THAM SỐ CHUYÊN SÂU", font=get_font(21, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((W / 2, 78), "ViGov-IE Event Ontology for Vietnamese Governance Knowledge Graph", font=get_font(14, bold=False), fill="#94A3B8", anchor="mm")

    # Center Event Node
    cx, cy = W / 2, 470
    draw_rounded_rect(draw, (cx - 160, cy - 70, cx + 160, cy + 70), radius=16, fill="#0284C7", outline="#0369A1", width=3)
    draw.text((cx, cy - 25), "NÚT SỰ KIỆN TRUNG TÂM", font=get_font(13, bold=True), fill="#BAE6FD", anchor="mm")
    draw.text((cx, cy + 2), ":Event (Reified Node)", font=get_font(20, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((cx, cy + 30), "event_type: BO_NHIEM | CHI_DAO | KY_LUAT...", font=get_font(11, bold=False), fill="#E0F2FE", anchor="mm")

    # Entity Nodes: Subject (Agent) on Left, Object (Target) on Right
    # Agent
    ax, ay = 180, cy
    draw_rounded_rect(draw, (ax - 130, ay - 60, ax + 130, ay + 60), radius=12, fill="#1E293B", outline="#0F172A", width=2)
    draw.text((ax, ay - 20), "CHỦ THỂ QUYẾT ĐỊNH", font=get_font(12, bold=True), fill="#94A3B8", anchor="mm")
    draw.text((ax, ay + 6), ":Organization / :Person", font=get_font(16, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((ax, ay + 30), "(e.g., Thủ tướng, Ban Bí thư)", font=get_font(11, bold=False), fill="#CBD5E1", anchor="mm")

    # Target
    tx, ty = W - 180, cy
    draw_rounded_rect(draw, (tx - 130, ty - 60, tx + 130, ty + 60), radius=12, fill="#1E293B", outline="#0F172A", width=2)
    draw.text((tx, ty - 20), "ĐỐI TƯỢNG TÁC ĐỘNG", font=get_font(12, bold=True), fill="#94A3B8", anchor="mm")
    draw.text((tx, ty + 6), ":Person / :Organization", font=get_font(16, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((tx, ty + 30), "(e.g., Cán bộ bổ nhiệm, Bộ ngành)", font=get_font(11, bold=False), fill="#CBD5E1", anchor="mm")

    # Connectors Agent -> Event -> Target
    draw.line([(ax + 130, ay), (cx - 160, cy)], fill="#0284C7", width=4)
    draw.polygon([(cx - 165, cy - 8), (cx - 165, cy + 8), (cx - 150, cy)], fill="#0284C7")
    draw.text(((ax + 130 + cx - 160) / 2, cy - 16), "ISSUED_BY", font=get_font(11, bold=True), fill="#0284C7", anchor="mm")

    draw.line([(cx + 160, cy), (tx - 130, ty)], fill="#0284C7", width=4)
    draw.polygon([(tx - 135, ty - 8), (tx - 135, ty + 8), (tx - 120, ty)], fill="#0284C7")
    draw.text(((cx + 160 + tx - 130) / 2, cy - 16), "TARGETS", font=get_font(11, bold=True), fill="#0284C7", anchor="mm")

    # 9 Specialized Arguments (surrounding cards)
    args_info = [
        # Top Row (3 items)
        ("1. legal_doc (Số hiệu văn bản)", "Quyết định, Chỉ thị, Nghị định, Kết luận TW\nVD: 'Quyết định số 1311/QĐ-TTg'\nĐộ chính xác: F1 = 99.4%", 220, 160, "#EFF6FF", "#3B82F6"),
        ("2. role (Chức danh bổ nhiệm)", "Chức vụ mới được bổ nhiệm (lọc sạch 'nguyên')\nVD: 'Thứ trưởng Bộ Khoa học và Công nghệ'\nĐộ chính xác: F1 = 97.2%", W / 2, 160, "#FDF2F8", "#EC4899"),
        ("3. appoint_type (Hình thức bổ nhiệm)", "Bổ nhiệm lại, Phê chuẩn, Chỉ định, Điều động\nVD: 'Điều động và bổ nhiệm'\nĐộ chính xác: F1 = 100.0%", W - 220, 160, "#F0FDF4", "#10B981"),
        # Middle Left & Right
        ("4. deadline (Thời hạn hoàn thành)", "Mốc thời gian quy định hoàn thành chỉ đạo\nVD: 'trước ngày 30/12', 'quý IV/2026'\nĐộ chính xác: F1 = 100.0%", 200, 310, "#FEF3C7", "#F59E0B"),
        ("5. urgency (Mức độ khẩn)", "Phó từ chỉ tính cấp bách của mệnh lệnh\nVD: 'khẩn trương', 'quyết liệt', 'nghiêm túc'\nĐộ chính xác: F1 = 100.0%", W - 200, 310, "#FEF2F2", "#EF4444"),
        # Bottom Row (4 items)
        ("6. penalty_form (Hình thức kỷ luật)", "Thứ bậc: Khai trừ > Cách chức > Cảnh cáo > Khiển trách\nVD: 'Khai trừ khỏi Đảng', 'Cách chức'\nĐộ chính xác: F1 = 97.8%", 200, 710, "#FEF2F2", "#DC2626"),
        ("7. action_content (Nội dung chỉ đạo)", "Mệnh đề hành động bảo tồn mục đích 'nhằm/để'\nVD: 'hoàn thiện thể chế nhằm tháo gỡ khó khăn'\nRecall: 86.3%", 530, 710, "#EFF6FF", "#2563EB"),
        ("8. tenure (Nhiệm kỳ bổ nhiệm)", "Thời hạn giữ chức vụ được ấn định\nVD: 'thời hạn 5 năm', 'nhiệm kỳ 2025-2030'\nĐộ chính xác: F1 = 98.2%", 850, 710, "#FAF5FF", "#8B5CF6"),
        ("9. violation_reason (Lý do vi phạm)", "Căn cứ hoặc hành vi sai phạm dẫn đến kỷ luật\nVD: 'vi phạm quy định của Đảng về phòng chống tham nhũng'\nĐộ chính xác: F1 = 94.6%", W - 180, 710, "#FFFBEB", "#D97706"),
    ]

    for title, desc, x, y, bg, border in args_info:
        bw, bh = 260, 100
        bx1, by1 = x - bw / 2, y - bh / 2
        bx2, by2 = x + bw / 2, y + bh / 2
        draw_rounded_rect(draw, (bx1, by1, bx2, by2), radius=8, fill=bg, outline=border, width=2)
        draw.text((bx1 + 10, by1 + 10), title, font=get_font(12, bold=True), fill="#0F172A")
        lines = desc.split("\n")
        ly = by1 + 32
        for l in lines:
            draw.text((bx1 + 10, ly), l, font=get_font(10, bold=False), fill="#475569")
            ly += 16
            
        # Draw connector line from box to event node
        line_color = border
        draw.line([(x, y + bh / 2 if y < cy else y - bh / 2), (cx, cy)], fill=line_color, width=1)

    # Re-draw Center Event Node on top to ensure clean border
    draw_rounded_rect(draw, (cx - 160, cy - 70, cx + 160, cy + 70), radius=16, fill="#0284C7", outline="#0369A1", width=3)
    draw.text((cx, cy - 25), "NÚT SỰ KIỆN TRUNG TÂM", font=get_font(13, bold=True), fill="#BAE6FD", anchor="mm")
    draw.text((cx, cy + 2), ":Event (Reified Node)", font=get_font(20, bold=True), fill="#FFFFFF", anchor="mm")
    draw.text((cx, cy + 30), "event_type: BO_NHIEM | CHI_DAO | KY_LUAT...", font=get_font(11, bold=False), fill="#E0F2FE", anchor="mm")

    img.save(FIG_DIR / "hinh3_khung_su_kien_n_ngoi.png", "PNG", dpi=(300, 300))
    print("✅ Đã tạo Hình 3: hinh3_khung_su_kien_n_ngoi.png")

if __name__ == "__main__":
    create_figure_1()
    create_figure_2()
    create_figure_3()
    print("🎉 Hoàn tất render toàn bộ 3 sơ đồ kiến trúc chuẩn khoa học!")
