import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figures_paper"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"],
    "font.size": 9,
    "axes.unicode_minus": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.20,
})

# Bảng màu chuẩn xuất bản khoa học
INK = "#0b0b0b"
INK2 = "#4a4946"
MUTED = "#7a7873"
GRID = "#e1e0d9"
LINE = "#8b8a84"
BLUE = "#1d6ec7"
ORANGE = "#d9571e"
BLUE_BG = "#eef5fc"
BLUE_DK = "#12427d"
BLUE_LT = "#7cb2f0"
GREY_BG = "#f5f4f0"
GREY_FILL = "#c5c4ba"
GOOD = "#0b730b"
BAD = "#c72c2c"
BAD_BG = "#fdf0f0"
GOOD_BG = "#edf7ed"
YEL_BG = "#fef8e7"


def canvas(w, h, xmax=100, ymax=100):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text="", fc="white", ec=LINE, lw=0.9, fs=8.5, bold=False,
        color=INK, ls="-", ha="center", va="center", pad=1.2, round_=0.8, zorder=2):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={round_}",
                       fc=fc, ec=ec, lw=lw, ls=ls, zorder=zorder)
    ax.add_patch(p)
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha=ha, va=va, fontsize=fs,
                fontweight="bold" if bold else "normal", color=color,
                linespacing=1.28, zorder=zorder + 1)
    return p


def arrow(ax, x1, y1, x2, y2, color=LINE, lw=1.1, style="-|>", ls="-", rad=0.0, ms=9):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                linestyle=ls, mutation_scale=ms,
                                connectionstyle=f"arc3,rad={rad}"),
                zorder=2)


def save(fig, name):
    path = OUT / name
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"Đã lưu: {path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Hình 1. Kiến trúc tổng thể hệ thống ViGov-IE v2.0
# ---------------------------------------------------------------------------
def fig1():
    fig, ax = canvas(8.4, 10.6, 106, 132)
    
    # 4 Dải tầng lớn (Layers)
    layers = [
        (98, 28, "TẦNG 1: THU THẬP DỮ LIỆU ĐA NGUỒN (KHÉP KÍN WIKIPEDIA → BÁO CHÍ)"),
        (69, 27, "TẦNG 2: TIỀN XỬ LÝ & LIÊN KẾT THỰC THỂ (WIKI GAZETTEER LÀM NEO)"),
        (35, 32, "TẦNG 3: ĐỘNG CƠ TRÍCH XUẤT SỰ KIỆN N-NGÔI (VIGOV-IE v2.0 - 12.671 CÂU/S)"),
        (3, 30, "TẦNG 4: HỢP NHẤT, KHỬ TRÙNG & LƯU TRỮ ĐỒ THỊ TRI THỨC (NEO4J 5.26)"),
    ]
    for y, h, title in layers:
        box(ax, 4, y, 98, h, fc=GREY_BG, ec="none", round_=1.2, zorder=0)
        # Header banner của tầng
        box(ax, 6, y + h - 4.5, 94, 3.8, title, fs=7.8, bold=True, fc=BLUE_DK, ec=BLUE_DK, color="white", round_=0.4)

    # --- TẦNG 1 (y: 98 -> 126)
    # Wikipedia (Trái) & Báo chí (Phải)
    w_col = 38.0
    x_left = 7.5
    x_right = 60.5
    
    # Box Wikipedia
    box(ax, x_left, 101, w_col, 19,
        "Wikipedia tiếng Việt\n(requests + MediaWiki API)\n"
        "• Duyệt BFS 3.134 trang chính khách\n"
        "• Regex bóc Infobox (| key = val):\n"
        "  1.798 Người · 1.181 Cơ quan",
        fs=7.0, fc="#fefce8", ec="#ca8a04", lw=1.2)
    
    # Box Báo chí
    box(ax, x_right, 101, w_col, 19,
        "Kho Báo chí Thời sự\n(feedparser & BeautifulSoup)\n"
        "• Luồng 1: Crawl chuyên mục chính luận\n"
        "• Luồng 2: Targeted RSS theo Wiki:\n"
        "  '\"[Tên Người]\" (bổ nhiệm | chỉ đạo...)'",
        fs=7.0, fc=BLUE_BG, ec=BLUE, lw=1.2)

    # Mũi tên khép kín Wiki -> Báo chí (Trái sang Phải)
    arrow(ax, x_left + w_col, 110.5, x_right, 110.5, color="#b45309", lw=1.6, style="-|>")
    ax.text(53.0, 112.5, "Targeted RSS\nQuery", ha="center", va="bottom", fontsize=6.6,
            fontweight="bold", color="#92400e", linespacing=1.1, zorder=4)

    # --- TẦNG 2 (y: 69 -> 96)
    # Gazetteer Wiki (Trái) & Tiền xử lý (Phải)
    box(ax, x_left, 81, w_col, 10,
        "Từ điển Thực thể Wiki (Hash Gazetteer O(1) RAM)\n"
        "1.798 Người · 1.181 Cơ quan · 1.563 Chức vụ\n"
        "Làm 'Khung neo' đối sánh định danh chính tắc duy nhất",
        fs=7.0, fc="#fefce8", ec="#ca8a04", lw=1.1)

    box(ax, x_right, 81, w_col, 10,
        "Tiền xử lý Ngữ liệu Báo chí (unicodedata & regex)\n"
        "• Chuẩn hóa Unicode NFC, thống nhất dấu thanh nguyên âm\n"
        "• Regex Lookbehind tách 442.314 câu (bảo vệ TP., PGS.TS.)",
        fs=7.0, fc="white", ec=LINE)

    # Mũi tên từ Tầng 1 xuống Tầng 2
    arrow(ax, x_left + w_col / 2, 101, x_left + w_col / 2, 91.5)
    arrow(ax, x_right + w_col / 2, 101, x_right + w_col / 2, 91.5)

    # Khối Hợp lưu Nhận diện & Liên kết thực thể
    box(ax, 7.5, 71, 91, 7.8,
        "NHẬN DIỆN & LIÊN KẾT THỰC THỂ: Aho-Corasick Longest Match + Canonical Slug\n"
        "Đối sánh từ điển Wiki gán ID chính tắc · Mẫu cú pháp ngữ cảnh bóc tách lãnh đạo/cơ quan mới",
        fs=7.1, fc="#fef3c7", ec="#d97706", lw=1.2, bold=True)
    arrow(ax, x_left + w_col / 2, 81, x_left + w_col / 2, 79.2)
    arrow(ax, x_right + w_col / 2, 81, x_right + w_col / 2, 79.2)

    # --- TẦNG 3 (y: 35 -> 67)
    # Phân loại sự kiện (Trái) & Trích xuất tham số chung (Phải)
    box(ax, x_left, 56.5, w_col, 8.5,
        "Phân loại Sự kiện (10 Loại)\n(Trigger Lexicon + Window 120 chars)\nBổ nhiệm, Kỷ luật, Chỉ đạo, Chủ trì...",
        fs=6.9, fc="white", ec=LINE)
    box(ax, x_right, 56.5, w_col, 8.5,
        "Trích xuất Tham số Chung (Regex)\n• legal_doc: \\d+/[A-ZĐ0-9\\-_]+ (99.4%)\n• deadline & urgency: Lexicon (100%)",
        fs=6.9, fc="white", ec=LINE)
    arrow(ax, 53.0, 71, 53.0, 65.5)
    arrow(ax, 53.0, 65.5, x_left + w_col / 2, 65.5)
    arrow(ax, 53.0, 65.5, x_right + w_col / 2, 65.5)

    # 3 Khối Rẽ nhánh nghiệp vụ Tầng 3
    w3 = 29.0
    gap3 = 2.0
    x3_1 = 7.5
    x3_2 = x3_1 + w3 + gap3
    x3_3 = x3_2 + w3 + gap3

    box(ax, x3_1, 37.5, w3, 14.5,
        "Sự kiện Nhân sự\n"
        "[Scoped Trie Matcher]\n"
        "• role: Tra cứu 1.563 chức vụ\n"
        "  sau 'giữ chức' (F1 97.2%)\n"
        "• appoint_type: Heuristic\n"
        "  13 động từ ghép (100%)",
        fs=6.8, fc=BLUE_BG, ec=BLUE)

    box(ax, x3_2, 37.5, w3, 14.5,
        "Sự kiện Kỷ luật\n"
        "[Multi-target Alignment]\n"
        "• penalty_form: Bảng 7 mức\n"
        "  kỷ luật Đảng/CQ (97.8%)\n"
        "• Delimiter (re.split) ghép cặp\n"
        "  1-1 danh sách nhiều người",
        fs=6.8, fc=BLUE_BG, ec=BLUE)

    box(ax, x3_3, 37.5, w3, 14.5,
        "Sự kiện Điều hành\n"
        "[Positional Masking]\n"
        "• Che <ORG> nhận lệnh\n"
        "• Regex Trimming lọc trợ từ\n"
        "• action_content dùng được\n"
        "  97.5% (gốc: 35.0%)",
        fs=6.8, fc=BLUE_BG, ec=BLUE)

    arrow(ax, x_left + w_col / 2, 56.5, x3_1 + w3 / 2, 52.5)
    arrow(ax, 53.0, 56.5, x3_2 + w3 / 2, 52.5)
    arrow(ax, x_right + w_col / 2, 56.5, x3_3 + w3 / 2, 52.5)

    # --- TẦNG 4 (y: 3 -> 33)
    # Mũi tên từ 3 nhánh xuống Tầng 4
    for xc in [x3_1 + w3 / 2, x3_2 + w3 / 2, x3_3 + w3 / 2]:
        arrow(ax, xc, 37.5, xc, 29.5)

    # Khối Khử trùng Partitioned Record Linkage v2
    box(ax, 7.5, 21.5, 91, 7.8,
        "KHỬ TRÙNG THỰC THỂ: Thuật toán Partitioned Record Linkage v2 (Xử lý trong 0,117 giây)\n"
        "Phân rã (Kind, Prefix, Core) + Chặn thể chế cứng (Đảng ≠ Chính quyền) → Độ chính xác 100,0% (4.583 cạnh)",
        fs=7.1, fc="#ecfdf5", ec="#059669", lw=1.2, bold=True)
    arrow(ax, 53.0, 21.5, 53.0, 17.5)

    # Khối Lưu trữ Neo4j
    box(ax, 7.5, 5.5, 91, 11.5,
        "ĐỒ THỊ TRI THỨC QUẢN LÝ NHÀ NƯỚC (Neo4j 5.26 Community + APOC + GDS 2.6)\n"
        "Khung cấu trúc từ Wikipedia  +  Nút sự kiện N-ngôi (:Event) mang 9 tham số từ Báo chí\n"
        "8.581 thực thể (5.438 người, 1.516 cơ quan, 1.563 chức vụ, 64 tỉnh) · 18.189 cạnh · 6.694 sự kiện",
        fs=7.2, fc="white", ec=BLUE_DK, lw=1.3)

    # Đường quan hệ cấu trúc từ Wikipedia đi thẳng vào đồ thị (Bên trái)
    dash = (0, (4, 3))
    ax.plot([x_left, 5.0, 5.0], [110.5, 110.5, 11.0], color=LINE, lw=1.1, ls=dash, zorder=1)
    arrow(ax, 5.0, 11.0, x_left, 11.0, ls=dash)
    ax.text(3.4, 55, "Cạnh cấu trúc tĩnh từ Wikipedia (giữ chức vụ, trực thuộc, cấp phó...)",
            rotation=90, fontsize=6.8, color=INK2, ha="center", va="center")

    save(fig, "hinh1_kien_truc_tong_the.png")


# ---------------------------------------------------------------------------
# Hình 2. Quan hệ nhị phân so với nút sự kiện N-ngôi
# ---------------------------------------------------------------------------
def fig2():
    # Canvas rộng rãi, xmax=110, ymax=75
    fig, ax = canvas(8.2, 5.4, 110, 75)
    box(ax, 4, 62, 102, 11.5, fc=GREY_BG, ec="none")
    ax.text(6, 71.0, "Câu nguồn (báo chí)", fontsize=7.8, color=INK2, fontweight="bold", va="center")
    ax.text(6, 65.8,
            "“Tại Quyết định số 397/QĐ-TTg ngày 25/2/2025, Thủ tướng điều động, bổ nhiệm Trung tướng Nguyễn Hải Trung,\n"
            "Giám đốc Công an thành phố Hà Nội giữ chức Thứ trưởng Bộ Dân tộc và Tôn giáo.”",
            fontsize=7.5, color=INK, va="center", style="italic", linespacing=1.35)

    # (a) nhị phân
    ax.text(4, 57.5, "(a) Biểu diễn nhị phân phẳng: Mất mát toàn bộ tham số ngữ cảnh", fontsize=8.6, fontweight="bold", color=INK)
    box(ax, 6, 44, 24, 8.5, "Thủ tướng\nChính phủ", fs=8.2)
    box(ax, 65, 44, 27, 8.5, "Nguyễn Hải Trung", fs=8.2)
    arrow(ax, 30, 48.2, 65, 48.2, color=INK2, lw=1.3)
    ax.text(47.5, 50.2, "BO_NHIEM", ha="center", fontsize=8.0, color=INK2, fontweight="bold")
    ax.text(6, 40.5, "Mô hình nhị phân không có thuộc tính lưu số quyết định, chức vụ mới, thời hạn.",
            fontsize=7.5, color=BAD, va="center")
    ax.plot([4, 106], [37.0, 37.0], color=GRID, lw=1)

    # (b) n-ngôi
    ax.text(4, 33.0, "(b) Biểu diễn N-ngôi: Kỹ thuật Event Reification trên Neo4j 5.26 Property Graph", fontsize=8.6, fontweight="bold", color=INK)
    box(ax, 6, 14, 22, 8.5, "Thủ tướng\nChính phủ", fs=8.2)
    box(ax, 38, 12, 22, 12.5, "Sự kiện\n(:Event)", fs=8.8, bold=True, fc=BLUE_BG, ec=BLUE, lw=1.4, round_=6)
    box(ax, 6, 1.5, 22, 7.5, "Nguyễn Hải Trung", fs=8.2)
    
    arrow(ax, 28, 18.2, 38, 18.2, color=INK2, lw=1.2)
    ax.text(33.0, 19.8, ":ISSUED_BY", ha="center", fontsize=7.2, color=BLUE_DK, fontweight="bold")
    
    ax.annotate("", xy=(28, 5.2), xytext=(45, 12),
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2, mutation_scale=9,
                                connectionstyle="arc3,rad=-0.15"))
    ax.text(40, 5.2, ":TARGETS", ha="left", fontsize=7.2, color=BLUE_DK, fontweight="bold")
    
    # Khung Card chứa 9 tham số trên nút (:Event)
    box(ax, 65, 1.0, 41, 26.5, "", fc="#f8fafc", ec="#93c5fd", lw=1.0, round_=0.8)
    ax.text(67, 25.2, "9 tham số lưu trữ trên nút (:Event)", fontsize=7.8, color=BLUE_DK, fontweight="bold")
    
    rows = [("legal_doc", "Quyết định số 397/QĐ-TTg"),
            ("appoint_type", "Điều động và bổ nhiệm"),
            ("role", "Thứ trưởng Bộ Dân tộc và Tôn giáo"),
            ("event_date", "2025-02-25")]
    x0, y0, rh = 67, 20.8, 4.9
    for i, (k, v) in enumerate(rows):
        y = y0 - i * rh
        box(ax, x0, y, 12.5, rh - 0.8, k, fs=7.0, fc=BLUE_BG, ec="none", round_=0.5)
        ax.text(x0 + 13.5, y + (rh - 0.8) / 2, v, fontsize=7.2, va="center", color=INK)
    ax.plot([60, 65], [18.2, 18.2], color=BLUE, lw=1.0)
    save(fig, "hinh2_su_kien_n_ngoi.png")


# ---------------------------------------------------------------------------
# Hình 3. Luồng xử lý bên trong bộ trích xuất ViGov-IE v2.0
# ---------------------------------------------------------------------------
def fig3():
    fig, ax = canvas(7.6, 7.4, 106, 104)
    box(ax, 21, 95, 64, 7.5, "ĐẦU VÀO: Câu đã gán nhãn thực thể · Loại sự kiện (Trigger Lexicon)", fs=8.0, fc=GREY_BG, ec=LINE)
    arrow(ax, 53, 95, 53, 90.5)
    
    box(ax, 4, 79.5, 98, 10.5,
        "BƯỚC 1 — Trích xuất tham số chung bằng Regex chuyên sâu & Từ điển\n"
        "• legal_doc: Regex số quyết định (\\d+/[A-ZĐ0-9\\-_]+) (F1 99.4%)\n"
        "• deadline: Regex mốc thời gian (F1 100%)  ·  urgency: Tra cứu Lexicon (F1 100%)",
        fs=7.6, fc=BLUE_BG, ec=BLUE)
    arrow(ax, 53, 79.5, 53, 74.0)
    
    box(ax, 25, 66.5, 56, 7.0, "BƯỚC 2 — Rẽ nhánh mô-đun chuyên biệt theo loại sự kiện", fs=8.2, bold=True, fc="white", ec=INK2)
    
    w_col = 30.5
    gap_col = 3.2
    cols = [
        (4.5, "Nhân sự", "BO_NHIEM · DIEU_DONG\nMIEN_NHIEM",
         [("appoint_type", "Heuristic ưu tiên 13 động từ ghép\n(điều động, bổ nhiệm... F1 100%)"),
          ("role", "Lookbehind sau “giữ chức/làm”\nkhớp từ điển 1.563 chức vụ (97.2%)"),
          ("tenure", "Regex nhiệm kỳ (\\d+ năm, \\d{4}-\\d{4})")]),
        (4.5 + w_col + gap_col, "Kỷ luật", "KY_LUAT",
         [("penalty_form", "Bảng 7 mức kỷ luật Đảng & CQ\nlấy mức nặng nhất khớp được (97.8%)"),
          ("violation_reason", "Regex sau “do / vì / vi phạm …”\nngắt ranh giới dấu chấm câu"),
          ("coordinated_items", "Token Delimiter (re.split)\nphân rã danh sách, ghép cặp 1-1")]),
        (4.5 + 2 * (w_col + gap_col), "Điều hành", "CHI_DAO · CHU_TRI\nPHOI_HOP · LAM_VIEC_VOI",
         [("action_content", ""),
          ("· CHI_DAO", "Positional Entity Masking <ORG>\nRegex Trimming loại đại từ, trợ từ"),
          ("· CHU_TRI, LAM_VIEC", "Regex bóc tên hội nghị,\ncuộc họp, buổi làm việc"),
          ("· PHOI_HOP", "Regex mệnh đề nội dung phối hợp")]),
    ]
    for x, title, types, items in cols:
        cx = x + w_col / 2
        arrow(ax, 53, 66.5, cx, 61.0)
        box(ax, x, 54.5, w_col, 6.5, "", fc=BLUE_DK, ec=BLUE_DK, round_=0.8)
        ax.text(cx, 57.75, title, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold", zorder=4)
        box(ax, x, 14, w_col, 40.5, "", fc="white", ec=BLUE, round_=0.8)
        ax.text(cx, 52.8, types, ha="center", va="top", fontsize=6.8, color=MUTED, linespacing=1.25, zorder=4)
        y = 46.0
        for k, d in items:
            ax.text(x + 1.2, y, k, ha="left", va="top", fontsize=7.3, color=BLUE_DK, fontweight="bold", zorder=4)
            y -= 2.4
            if d:
                ax.text(x + 1.2, y, d, ha="left", va="top", fontsize=6.9, color=INK, linespacing=1.2, zorder=4)
                y -= 2.2 * (d.count("\n") + 1)
            y -= 1.4
        arrow(ax, cx, 14, 53, 9.2)
    box(ax, 21, 2.5, 64, 6.5, "ĐẦU RA: Bản ghi tham số sự kiện N-ngôi nạp Neo4j (12.671 câu/s)", fs=8.0, fc=GREY_BG, ec=LINE)
    save(fig, "hinh3_luong_trich_xuat.png")


# ---------------------------------------------------------------------------
# Hình 4. Ví dụ từng bước: action_content
# ---------------------------------------------------------------------------
def fig4():
    fig, ax = canvas(7.6, 5.6, 106, 78)
    ax.set_ylim(-3, 75)
    steps = [
        ("Câu nguồn gốc:",
         "Chỉ đạo một số nhiệm vụ cụ thể, Thủ tướng yêu cầu Bộ Xây dựng tiếp tục nghiên cứu, rà soát,\n"
         "hoàn thiện các văn bản quy phạm pháp luật để tháo gỡ khó khăn, vướng mắc phát sinh trong thực tiễn, …",
         GREY_BG, LINE),
        ("Thao tác 1. Cắt sau từ kích hoạt chỉ đạo bằng Regex [re.search]:",
         "Bộ Xây dựng tiếp tục nghiên cứu, rà soát, hoàn thiện các văn bản quy phạm pháp luật để tháo gỡ …",
         "white", LINE),
        ("Thao tác 2. Positional Masking che <TARGET> và Regex Strip trợ từ đệm:",
         "nghiên cứu, rà soát, hoàn thiện các văn bản quy phạm pháp luật để tháo gỡ …",
         "white", LINE),
        ("Thao tác 3. Tách vị ngữ hành động bằng mẫu ngắt ranh giới cú pháp [re.split]:",
         "nghiên cứu, rà soát, hoàn thiện các văn bản quy phạm pháp luật",
         BLUE_BG, BLUE),
    ]
    y = 73
    for i, (title, text, fc, ec) in enumerate(steps):
        h = 12.0 if i == 0 else 9.2
        y -= h
        box(ax, 4, y, 98, h, "", fc=fc, ec=ec, round_=0.8)
        ax.text(6, y + h - 2.4, title, fontsize=7.4, fontweight="bold", color=BLUE_DK if i else INK2, va="center")
        ax.text(6, y + (h - 4) / 2 + 0.2, text, fontsize=7.8, color=INK, va="center", linespacing=1.35,
                fontweight="bold" if i == 3 else "normal")
        if i < 3:
            arrow(ax, 53, y, 53, y - 3.2)
        y -= 3.4

    # So sánh với hệ cơ sở
    y -= 1.5
    ax.text(4, y, "Đầu ra của hệ cơ sở (underthesea chunking cú pháp):",
            fontsize=7.8, color=INK2, fontweight="bold", va="center")
    box(ax, 4, y - 11.2, 98, 9.2,
        "một số nhiệm vụ cụ thể , Thủ tướng yêu cầu Bộ Xây dựng tiếp tục nghiên cứu , rà soát ,\n"
        "hoàn thiện các văn bản quy phạm pháp luật",
        fs=7.8, fc=BAD_BG, ec=BAD, color=INK)
    ax.text(4, y - 14.5, "→ underthesea lẫn trạng ngữ mở đầu, chủ thể, từ kích hoạt và cơ quan nhận lệnh (chỉ 35% dùng được).",
            fontsize=7.3, color=BAD, va="center")
    save(fig, "hinh4_vi_du_action_content.png")


# ---------------------------------------------------------------------------
# Hình 5. Hai cạm bẫy và Giải pháp Partitioned Record Linkage v2
# ---------------------------------------------------------------------------
def fig5():
    fig, ax = canvas(7.6, 10.0, 106, 140)

    def parts(y, kind, prefix, core, core_fc):
        box(ax, 19, y, 9, 5.2, kind, fs=7.4, fc="white", ec=LINE, round_=0.5)
        box(ax, 29, y, 38, 5.2, prefix, fs=7.4, fc="white", ec=LINE, round_=0.5)
        box(ax, 68, y, 15, 5.2, core, fs=7.4, bold=True, fc=core_fc, ec=LINE, round_=0.5)

    def header(y):
        for x, w, t in ((19, 9, "Loại"), (29, 38, "Tiền tố (loại hình cơ quan)"), (68, 15, "Tên lõi")):
            ax.text(x + w / 2, y, t, ha="center", fontsize=7.1, color=MUTED)

    # ---- (a)
    ax.text(4, 134.5, "(a) Bẫy trùng tiền tố — So khớp mờ chuỗi (RapidFuzz / Token Set Ratio)",
            fontsize=8.6, fontweight="bold")
    header(128.8)
    ax.text(4, 124.2, "UBND TP Hà Nội", fontsize=7.8, va="center")
    parts(121.5, "org", "uy_ban_nhan_dan_thanh_pho", "ha_noi", YEL_BG)
    ax.text(4, 117.2, "UBND TP Cần Thơ", fontsize=7.8, va="center")
    parts(114.5, "org", "uy_ban_nhan_dan_thanh_pho", "can_tho", YEL_BG)
    
    ax.text(85, 124.2, "tên lõi khác nhau", fontsize=7.2, color=INK2, va="center")
    ax.text(85, 117.2, "tiền tố giống hệt", fontsize=7.2, color=INK2, va="center")
    
    box(ax, 4, 99.5, 48, 11.5,
        "So khớp mờ RapidFuzz Token Set Ratio\nđộ tương đồng = 90,4  ≥  ngưỡng 85\n→ GỘP NHẦM TAI HẠI (Lỗi 100%)",
        fs=7.6, fc=BAD_BG, ec=BAD)
    box(ax, 54, 99.5, 48, 11.5,
        "Luật phân rã đặc trưng: so tên lõi trước\nha_noi  ≠  can_tho\n→ CHẶN ĐÚNG TUYỆT ĐỐI",
        fs=7.6, fc=GOOD_BG, ec=GOOD)
    ax.plot([4, 102], [95.5, 95.5], color=GRID, lw=1)

    # ---- (b)
    ax.text(4, 91.0, "(b) Bẫy cùng địa phương — So khớp tiền tố bằng tập con (Subset Trap)",
            fontsize=8.6, fontweight="bold")
    header(85.3)
    ax.text(4, 80.7, "Tỉnh ủy Đồng Nai", fontsize=7.8, va="center")
    parts(78.0, "org", "tinh_uy", "dong_nai", YEL_BG)
    ax.text(4, 73.7, "UBND tỉnh Đồng Nai", fontsize=7.8, va="center")
    parts(71.0, "org", "uy_ban_nhan_dan_tinh", "dong_nai", YEL_BG)
    
    ax.text(85, 80.7, "tên lõi trùng nhau", fontsize=7.2, color=INK2, va="center")
    ax.text(85, 73.7, "tiền tố khác nhau", fontsize=7.2, color=INK2, va="center")
    
    box(ax, 4, 53.5, 98, 13.5,
        "Luật ngây thơ: tên lõi trùng → so tiền tố bằng token_set_ratio với ngưỡng 80\n"
        "{tinh, uy}  là tập con của  {uy, ban, nhan, dan, tinh}   →   độ tương đồng = 100\n"
        "→ GỘP NHẦM Tỉnh ủy với Ủy ban nhân dân tỉnh (sai 98/108 cặp)",
        fs=7.6, fc=BAD_BG, ec=BAD)
    ax.plot([4, 102], [49.5, 49.5], color=GRID, lw=1)

    # ---- (c)
    ax.text(4, 45.0, "(c) Giải pháp hoàn thiện: Thuật toán Partitioned Record Linkage v2 (Độ chính xác 100%)",
            fontsize=8.6, fontweight="bold", color=GOOD)
    box(ax, 4, 11.5, 98, 30.0, "", fc=GOOD_BG, ec=GOOD, lw=1.2)
    ax.text(6, 38.0, "NGUYÊN TẮC HOẠT ĐỘNG CỦA THUẬT TOÁN:", fontsize=7.8, fontweight="bold", color=GOOD)
    
    lines_c = [
        "1. Phân rã 3 thành phần: Entity Slug = (Kind, Prefix_Context, Core_Name).",
        "2. Chặn thể chế cứng (Hard Blocking): Đảng (tinh_uy) ≠ Chính quyền (ubnd) → TUYỆT ĐỐI KHÔNG GỘP.",
        "3. So khớp Tên lõi địa phương: ha_noi ≠ can_tho → Giữ nguyên tách biệt (triệt tiêu 100% bẫy (a)).",
        "4. Bảng ánh xạ bí danh (config/org_aliases.json): tp_hcm → tp_ho_chi_minh, so_kh_va_dt → so_ke_hoach...",
        "5. Kết quả kiểm định trên 8.937 cạnh: Độ chính xác 100.0% (0 lỗi sai), gộp an toàn 4.583 cạnh trong 0,117s."
    ]
    cy = 34.0
    for l in lines_c:
        ax.text(7, cy, l, fontsize=7.2, color=INK, va="center")
        cy -= 4.4

    ax.text(4, 5.5, "Thuật toán Partitioned Record Linkage v2 thay thế hoàn toàn so khớp mờ ngây thơ,",
            fontsize=7.4, color=INK2, va="center", fontweight="bold")
    ax.text(4, 2.2, "giải quyết triệt để cả hai bẫy (a) và (b), đạt độ chính xác 100,0% trên 8.937 cạnh kiểm định.",
            fontsize=7.4, color=GOOD, va="center", fontweight="bold")

    save(fig, "hinh5_hai_bay_khu_trung.png")


# ---------------------------------------------------------------------------
# Hình 6. F1 Score theo từng trường tham số
# ---------------------------------------------------------------------------
def fig6():
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    fields = ["Số văn bản\n(legal_doc)", "Thời hạn\n(deadline)", "Mức khẩn\n(urgency)",
              "Hình thức\n(appoint_type)", "Hình thức KL\n(penalty_form)", "Chức vụ\n(role)"]
    f1_base = [99.7, 95.8, 86.4, 100.0, 99.4, 99.4]
    f1_opt  = [99.4, 100.0, 100.0, 100.0, 97.8, 97.2]
    import numpy as np
    x = np.arange(len(fields))
    w = 0.32
    ax.bar(x - w / 2, f1_base, w, label="Hệ cơ sở (underthesea chunker)", color=BLUE, zorder=3)
    ax.bar(x + w / 2, f1_opt,  w, label="ViGov-IE v2 (Động cơ luật chuyên sâu)", color=ORANGE, zorder=3)
    
    for i in range(len(fields)):
        v_b = f1_base[i]
        v_o = f1_opt[i]
        if abs(v_b - v_o) < 0.8:
            ax.text(x[i] - w / 2, v_b + 0.6, f"{v_b:.1f}%", ha="center", fontsize=6.8, color=INK2)
            ax.text(x[i] + w / 2, v_o + 2.2, f"{v_o:.1f}%", ha="center", fontsize=7.0, color=INK, fontweight="bold")
        else:
            ax.text(x[i] - w / 2, v_b + 0.8, f"{v_b:.1f}%", ha="center", fontsize=6.8, color=INK2)
            ax.text(x[i] + w / 2, v_o + 0.8, f"{v_o:.1f}%", ha="center", fontsize=7.0, color=INK, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(fields, fontsize=7.5)
    ax.set_xlim(-0.7, len(fields) - 0.3)
    ax.set_ylim(75, 106)
    ax.set_ylabel("F1 Score (%)", fontsize=8.2)
    ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="lower left", fontsize=7.8, frameon=True, edgecolor=GRID)
    save(fig, "hinh6_f1_theo_truong.png")


# ---------------------------------------------------------------------------
# Hình 7. Rà soát thủ công nội dung chỉ đạo trên 40 câu
# ---------------------------------------------------------------------------
def fig7():
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    cats = ["Sạch, dùng được ngay", "Dùng được (dính tiền tố)", "Bị cụt / thiếu", "Lẫn chủ thể / sai"]
    base_vals = [6, 8, 17, 9]     # 14 / 40 dùng được (35.0%)
    opt_vals  = [29, 10, 0, 1]    # 39 / 40 dùng được (97.5%)
    import numpy as np
    x = np.arange(len(cats))
    w = 0.34
    ax.bar(x - w / 2, base_vals, w, label="Hệ cơ sở (underthesea chunker)", color=BLUE, zorder=3)
    ax.bar(x + w / 2, opt_vals,  w, label="ViGov-IE v2 (Positional Masking)", color=ORANGE, zorder=3)
    for i in range(len(cats)):
        ax.text(x[i] - w / 2, base_vals[i] + 0.6, str(base_vals[i]), ha="center", fontsize=7.6, color=INK2)
        ax.text(x[i] + w / 2, opt_vals[i] + 0.6,  str(opt_vals[i]),  ha="center", fontsize=7.6, color=INK, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=7.4)
    ax.set_xlim(-0.6, len(cats) - 0.4)
    ax.set_ylim(0, 35)
    ax.set_ylabel("Số câu (trên 40 câu rà soát)", fontsize=8.2)
    ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper right", fontsize=7.8, frameon=True, edgecolor=GRID)
    save(fig, "hinh7_ra_soat_thu_cong.png")


# ---------------------------------------------------------------------------
# Hình 8. Kết quả khử trùng tên cơ quan
# ---------------------------------------------------------------------------
def fig8():
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={"width_ratios": [1.05, 1], "wspace": 0.5})
    labels = ["Cạnh thô", "Gộp trùng khớp\nchính xác", "Partitioned\nRecord Linkage"]
    vals = [8937, 4758, 4583]
    a.bar(range(3), vals, width=0.52, color=[GREY_FILL, BLUE, GOOD], zorder=3)
    for i, v in enumerate(vals):
        a.text(i, v + 180, f"{v:,}".replace(",", "."), ha="center", fontsize=8.4, color=INK, fontweight="bold" if i == 2 else "normal")
    a.set_xticks(range(3))
    a.set_xticklabels(labels, fontsize=7.6)
    a.set_xlim(-0.6, 2.6)
    a.set_ylim(0, 10400)
    a.set_yticks([0, 2500, 5000, 7500, 10000])
    a.set_yticklabels(["0", "2.500", "5.000", "7.500", "10.000"], fontsize=7.6)
    a.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    a.set_title("(a) Số cạnh tin tức sau mỗi bước", fontsize=8.4, loc="left", color=INK, pad=8)
    
    cats = [("Chính xác: Hợp nhất an toàn (0 lỗi sai)", 4354, GOOD, "white"),
            ("Chặn đúng: Hai cơ quan khác địa phương", 1422, BLUE_LT, INK),
            ("Chặn đúng: Đảng ≠ Chính quyền cùng tỉnh", 98, BLUE_DK, "white")]
    for i, (name, v, c, tc) in enumerate(cats):
        y = 2 - i
        b.barh(y, v, height=0.5, color=c, zorder=3)
        b.text(v + 80, y, str(v), va="center", fontsize=8.0, color=INK, fontweight="bold")
        b.text(0, y + 0.42, name, va="center", fontsize=7.3, color=INK2)
    b.set_xlim(0, 5200)
    b.set_ylim(-0.5, 2.9)
    b.set_yticks([])
    b.set_xticks([0, 1000, 2500, 4000, 5000])
    b.tick_params(axis="x", labelsize=7.4)
    b.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    b.set_title("(b) Kiểm định thuật toán Partitioned Linkage", fontsize=8.4, loc="left", color=INK, pad=8)
    for p_ax in (a, b):
        p_ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            p_ax.spines[s].set_visible(False)
        p_ax.spines["bottom"].set_color(GREY_FILL)
        p_ax.tick_params(axis="both", length=0, colors=INK2)
    save(fig, "hinh8_ket_qua_khu_trung.png")


# ---------------------------------------------------------------------------
# Hình 9, 10 (báo cáo học phần): phân bố loại quan hệ và phân bố bậc
# ---------------------------------------------------------------------------
def _stats():
    import json
    p = ROOT / "report" / "network_stats.json"
    if p.exists():
        return json.load(open(p, encoding="utf-8"))
    return None


def fig9():
    S = _stats()
    if not S:
        return
    rt = sorted(S["rel_types"].items(), key=lambda kv: kv[1])
    names, vals = [k for k, _ in rt], [v for _, v in rt]
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    import numpy as np
    y = np.arange(len(names))
    ax.barh(y, vals, height=0.62, color=BLUE, zorder=3)
    for i, v in enumerate(vals):
        ax.text(v + 60, i, f"{v:,}".replace(",", "."), va="center", fontsize=7.6, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7.8)
    ax.set_xlim(0, max(vals) * 1.15)
    ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Số cạnh", fontsize=8.2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "hinh9_canh_theo_loai.png")


def fig10():
    S = _stats()
    if not S:
        return
    dh = S["base_graph"]["degree_hist"]
    xs = [k for k, v in dh if k > 0 and v > 0]
    ys = [v for k, v in dh if k > 0 and v > 0]
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    ax.scatter(xs, ys, s=16, color=BLUE, alpha=0.8, edgecolors="none")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Bậc của nút (thang log)", fontsize=8.2)
    ax.set_ylabel("Số lượng nút (thang log)", fontsize=8.2)
    ax.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "hinh10_phan_bo_bac.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    fig6()
    fig7()
    fig8()
    fig9()
    fig10()
