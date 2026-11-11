# -*- coding: utf-8 -*-
"""
Sinh bộ hình cho báo cáo nghiên cứu ViGov-IE (bản đã kiểm định).
Đầu ra: report/figures_paper/hinh1..hinh10 (PNG 300 DPI).

Mọi con số trong hình lấy từ kết quả đo lại bằng scratch/verify_claims.py và
scratch/verify_dedup.py (xem Phụ lục A của báo cáo).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figures_paper"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"],
    "font.size": 9,
    "axes.unicode_minus": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08,
})

# Bảng màu: trung tính + 2 màu định danh (đã kiểm tra tương phản và mù màu)
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
LINE = "#8b8a84"
BLUE = "#2a78d6"      # hệ cơ sở (baseline)
ORANGE = "#eb6834"    # ViGov-IE v2
BLUE_BG = "#e8f1fc"
BLUE_DK = "#184f95"
BLUE_LT = "#86b6ef"
GREY_BG = "#f4f3ef"
GREY_FILL = "#c3c2b7"
GOOD = "#0c7a0c"
BAD = "#d03b3b"
BAD_BG = "#fbeaea"
GOOD_BG = "#e9f5e9"
YEL_BG = "#fdf3d7"


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
                linespacing=1.25, zorder=zorder + 1)
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
# Hình 1. Kiến trúc tổng thể: Wikipedia -> Targeted Crawling & Entity Linker
# ---------------------------------------------------------------------------
def fig1():
    fig, ax = canvas(7.6, 9.4, 106, 126)
    bands = [
        (97, 27, "1", "THU THẬP DỮ LIỆU\n(requests, feedparser)"),
        (67, 28, "2", "TIỀN XỬ LÝ & LIÊN KẾT\n(unicodedata, regex)"),
        (33, 32, "3", "TRÍCH XUẤT THAM SỐ\n(ViGov-IE v2 Engine)"),
        (2, 29, "4", "HỢP NHẤT & LƯU TRỮ\n(Neo4j, Partitioned)"),
    ]
    for y, h, num, name in bands:
        box(ax, 0, y, 106, h, fc=GREY_BG, ec="none", round_=1.2, zorder=0)
        ax.add_patch(Circle((4.4, y + h - 4.6), 2.3, fc=BLUE_DK, ec="none", zorder=3))
        ax.text(4.4, y + h - 4.65, num, ha="center", va="center", color="white",
                fontsize=9.5, fontweight="bold", zorder=4)
        ax.text(8.4, y + h - 3.1, name, ha="left", va="top", fontsize=7.8,
                fontweight="bold", color=BLUE_DK, linespacing=1.3)
    L, R, W = 25, 66, 36          # hai cột: báo chí (trái), Wikipedia (phải)
    FW = R + W - L                # bề rộng khối trải hai cột

    # Tầng 1: Thu thập dữ liệu
    box(ax, R, 99, W, 23, 
        "Wikipedia tiếng Việt (requests + MediaWiki API)\n"
        "• Duyệt BFS cây thể loại: 3.134 trang chính khách\n"
        "• Regex bóc Infobox (| key = val):\n"
        "  1.798 Lãnh đạo · 1.181 Cơ quan · 1.563 Chức vụ", 
        fs=7.2, fc="#fefce8", ec="#ca8a04", lw=1.2)
    
    box(ax, L, 99, W, 23, 
        "Kho Báo chí Thời sự (feedparser & BeautifulSoup)\n"
        "• Luồng 1: Crawl chuyên mục chính luận (16.757 bài)\n"
        "• Luồng 2: Targeted RSS theo danh sách Wiki:\n"
        "  '\"[Tên Người]\" (bổ nhiệm OR chỉ đạo OR kỷ luật...)'", 
        fs=7.2, fc=BLUE_BG, ec=BLUE, lw=1.2)

    # MŨI TÊN LIÊN KẾT 1: Wiki -> Targeted Crawling của Báo chí
    arrow(ax, R, 110.5, L + W, 110.5, color="#b45309", lw=1.5, style="-|>")
    ax.text((L + W + R) / 2, 112.5, "Lấy tên người từ Wiki\nsinh query Google News RSS", 
            ha="center", va="bottom", fontsize=6.8, color="#b45309", fontweight="bold", linespacing=1.15)

    # Tầng 2: Tiền xử lý & Liên kết thực thể
    box(ax, R, 80, W, 13.5, 
        "Từ điển Thực thể Wiki (Hash Gazetteer O(1))\n"
        "1.798 Người · 1.181 Cơ quan · 1.563 Chức vụ\n"
        "Làm 'Khung neo' đối sánh định danh chính tắc", 
        fs=7.1, fc="#fefce8", ec="#ca8a04", lw=1.1)

    box(ax, L, 80, W, 13.5, 
        "Tiền xử lý Ngữ liệu (unicodedata & regex)\n"
        "• Chuẩn hóa Unicode NFC, thống nhất dấu thanh\n"
        "• Regex Lookbehind tách 442.314 câu (bảo vệ TP., PGS.TS.)", 
        fs=7.1, fc="white", ec=LINE)

    # Mũi tên từ Tầng 1 xuống Tầng 2
    arrow(ax, L + W / 2, 99, L + W / 2, 94.0)
    arrow(ax, R + W / 2, 99, R + W / 2, 94.0)

    # Khối Hợp lưu Nhận diện & Liên kết thực thể
    box(ax, L, 69.5, FW, 9.0, 
        "NHẬN DIỆN VÀ LIÊN KẾT THỰC THỂ (Aho-Corasick & Context Heuristics)\n"
        "Khớp tên trong báo vào Gazetteer Wiki → Gán ID Wiki chính tắc;\n"
        "Người mới ngoài Wiki → Heuristic nhận diện ngữ cảnh chức vụ sinh mã 'per:news:...'", 
        fs=7.0, fc=BLUE_BG, ec=BLUE_DK, lw=1.3, bold=True)

    arrow(ax, L + W / 2, 80, L + W / 2, 78.8)
    arrow(ax, R + W / 2, 80, R + W / 2, 78.8)

    # Tầng 3: Động cơ trích xuất sự kiện N-ngôi
    mid = L + FW / 2
    arrow(ax, mid, 69.5, mid, 63.0)
    ax.text(mid + 1.5, 66.2, "Phân loại 10 sự kiện (Trigger Lexicon Dictionary, cửa sổ 120 ký tự)", fontsize=7.1, color=INK2, va="center")
    box(ax, L, 54.5, FW, 8.0, 
        "ĐỘNG CƠ TRÍCH XUẤT VIGOV-IE v2.0 (12.671 câu/giây trên CPU)\n"
        "Luật dùng chung (Regex): legal_doc (F1 99.4%)  ·  deadline (100%)  ·  urgency (100%)", 
        fs=7.3, fc=BLUE_BG, ec=BLUE, bold=True)
    
    bw = (FW - 4) / 3
    xs = [L, L + bw + 2, L + 2 * bw + 4]
    txt = ["Sự kiện nhân sự\nScoped Trie Matcher (1.563 chức vụ)\nappoint_type (100%) · role (97.2%)\nRegex tách nhiệm kỳ tenure",
           "Sự kiện kỷ luật\nBảng 7 hình thức kỷ luật Đảng & CQ\nToken Delimiter (re.split) ghép 1-1\npenalty_form (97.8%) · violation_reason",
           "Chỉ đạo · chủ trì · phối hợp\nPositional Entity Masking\nRegex Stripping loại đại từ, trợ từ\naction_content sạch 97.5%"]
    for x, t in zip(xs, txt):
        box(ax, x, 35, bw, 16.5, t, fs=6.9, fc=BLUE_BG, ec=BLUE)
        arrow(ax, x + bw / 2, 54.5, x + bw / 2, 51.8)
        arrow(ax, x + bw / 2, 35, x + bw / 2, 27.5)

    # Tầng 4: Hợp nhất & Lưu trữ Đồ thị
    box(ax, L, 18.5, FW, 8.5, 
        "KHỬ TRÙNG THỰC THỂ: Thuật toán Partitioned Record Linkage v2 (0.117 giây)\n"
        "Phân rã 3 thành phần (Kind, Prefix, Core) + Chặn thể chế cứng (Đảng ≠ CQ) → Độ chính xác 100%", 
        fs=7.1, fc="#ecfdf5", ec="#059669", lw=1.2, bold=True)
    arrow(ax, mid, 18.5, mid, 15.0)
    box(ax, L, 3.5, FW, 11.5,
        "ĐỒ THỊ TRI THỨC QUẢN LÝ NHÀ NƯỚC (Neo4j 5.26 Community + APOC + GDS 2.6)\n"
        "Khung cấu trúc từ Wikipedia  +  Nút sự kiện N-ngôi mang 9 tham số từ Báo chí\n"
        "5.438 người · 1.516 cơ quan · 1.563 chức vụ · 64 tỉnh/thành · 6.694 sự kiện · 18.189 cạnh", 
        fs=7.2, fc="white", ec=BLUE_DK, lw=1.3)

    # Quan hệ cấu trúc từ Wikipedia đi thẳng vào đồ thị
    xr = R + W + 2.4
    dash = (0, (4, 3))
    ax.plot([R + W, xr, xr], [110, 110, 8.5], color=LINE, lw=1.1, ls=dash, zorder=1)
    arrow(ax, xr, 8.5, R + W, 8.5, ls=dash)
    ax.text(xr + 2.0, 58, "Cạnh cấu trúc tĩnh lấy từ Wikipedia (giữ chức vụ, trực thuộc, kế nhiệm, ...)",
            rotation=90, fontsize=7.1, color=INK2, ha="center", va="center")
    save(fig, "hinh1_kien_truc_tong_the.png")


# ---------------------------------------------------------------------------
# Hình 2. Quan hệ nhị phân so với nút sự kiện N-ngôi
# ---------------------------------------------------------------------------
def fig2():
    fig, ax = canvas(7.0, 5.2, 100, 75)
    box(ax, 0, 62, 100, 11.5, fc=GREY_BG, ec="none")
    ax.text(2, 71.0, "Câu nguồn (báo chí)", fontsize=7.8, color=INK2, fontweight="bold", va="center")
    ax.text(2, 65.8,
            "“Tại Quyết định số 397/QĐ-TTg ngày 25/2/2025, Thủ tướng điều động, bổ nhiệm Trung tướng Nguyễn Hải Trung,\n"
            "Giám đốc Công an thành phố Hà Nội giữ chức Thứ trưởng Bộ Dân tộc và Tôn giáo.”",
            fontsize=7.6, color=INK, va="center", style="italic", linespacing=1.4)

    # (a) nhị phân
    ax.text(0, 57.5, "(a) Biểu diễn nhị phân phẳng: mất mát toàn bộ tham số ngữ cảnh", fontsize=8.6, fontweight="bold", color=INK)
    box(ax, 4, 45, 22, 8, "Thủ tướng\nChính phủ", fs=8.2)
    box(ax, 58, 45, 24, 8, "Nguyễn Hải Trung", fs=8.2)
    arrow(ax, 26, 49, 58, 49, color=INK2, lw=1.3)
    ax.text(42, 50.8, "BO_NHIEM", ha="center", fontsize=8, color=INK2, fontweight="bold")
    ax.text(4, 41.2, "Mô hình nhị phân không có thuộc tính lưu số quyết định, chức vụ mới, thời hạn.",
            fontsize=7.6, color=BAD, va="center")
    ax.plot([0, 100], [37.5, 37.5], color=GRID, lw=1)

    # (b) n-ngôi
    ax.text(0, 33, "(b) Biểu diễn N-ngôi: Kỹ thuật Event Reification trên Neo4j 5.26 Property Graph", fontsize=8.6, fontweight="bold", color=INK)
    box(ax, 2, 14, 19, 8, "Thủ tướng\nChính phủ", fs=8.2)
    box(ax, 34, 12, 21, 12, "Sự kiện\n(:Event)", fs=8.8, bold=True, fc=BLUE_BG, ec=BLUE, lw=1.4, round_=6)
    box(ax, 2, 1.5, 19, 7, "Nguyễn Hải Trung", fs=8.2)
    arrow(ax, 21, 18, 34, 18, color=INK2, lw=1.2)
    ax.text(27.5, 19.6, ":ISSUED_BY", ha="center", fontsize=7.2, color=BLUE_DK, fontweight="bold")
    ax.annotate("", xy=(21, 5), xytext=(41, 12),
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2, mutation_scale=9,
                                connectionstyle="arc3,rad=-0.15"))
    ax.text(38, 5.2, ":TARGETS", ha="left", fontsize=7.2, color=BLUE_DK, fontweight="bold")
    rows = [("legal_doc", "Quyết định số 397/QĐ-TTg"),
            ("appoint_type", "Điều động và bổ nhiệm"),
            ("role", "Thứ trưởng Bộ Dân tộc và Tôn giáo"),
            ("event_date", "2025-02-25")]
    x0, y0, rh = 61, 23.5, 5.2
    ax.text(x0, y0 + 3.8, "9 tham số lưu trữ trên nút (:Event)", fontsize=7.8, color=INK2, fontweight="bold")
    for i, (k, v) in enumerate(rows):
        y = y0 - (i + 1) * rh + 1.2
        box(ax, x0, y, 12.5, rh - 0.8, k, fs=7.4, fc=BLUE_BG, ec="none", round_=0.5)
        ax.text(x0 + 13.6, y + (rh - 0.8) / 2, v, fontsize=7.6, va="center", color=INK)
    ax.plot([55, 60.2], [18, 14.5], color=BLUE, lw=1.0)
    ax.plot([60.2, 60.2], [3.5, 25.5], color=BLUE, lw=1.0)
    save(fig, "hinh2_su_kien_n_ngoi.png")


# ---------------------------------------------------------------------------
# Hình 3. Luồng xử lý bên trong bộ trích xuất
# ---------------------------------------------------------------------------
def fig3():
    fig, ax = canvas(7.2, 7.2, 100, 102)
    box(ax, 20, 93, 60, 8, "ĐẦU VÀO: Câu đã gán nhãn thực thể · Loại sự kiện (Trigger Lexicon)", fs=8.2, fc=GREY_BG, ec=LINE)
    arrow(ax, 50, 93, 50, 88.2)
    box(ax, 5, 77, 90, 11,
        "BƯỚC 1 — Trích xuất tham số chung bằng Regex & Từ điển chuyên sâu (ViGov-IE v2)\n"
        "• legal_doc: Regex số quyết định (\\d+/[A-ZĐ0-9\\-_]+) (F1 99.4%)\n"
        "• deadline: Regex mốc thời hạn (trước ngày \\d+/\\d+, quý [I-IV]) (F1 100%)  ·  urgency: Lexicon (100%)",
        fs=7.8, fc=BLUE_BG, ec=BLUE)
    arrow(ax, 50, 77, 50, 71.5)
    box(ax, 24, 64, 52, 7.5, "BƯỚC 2 — Rẽ nhánh mô-đun chuyên biệt theo loại sự kiện", fs=8.2, bold=True, fc="white", ec=INK2)
    cols = [
        (0, "Nhân sự", "BO_NHIEM · DIEU_DONG\nMIEN_NHIEM",
         [("appoint_type", "Heuristic ưu tiên 13 động từ ghép\n(điều động, bổ nhiệm... F1 100%)"),
          ("role", "Lookbehind sau “giữ chức/làm”\nkhớp từ điển 1.563 chức vụ (97.2%)"),
          ("tenure", "Regex nhiệm kỳ (\\d+ năm, \\d{4}-\\d{4})")]),
        (34.5, "Kỷ luật", "KY_LUAT",
         [("penalty_form", "Bảng 7 hình thức kỷ luật Đảng & CQ\nlấy mức nặng nhất khớp được (97.8%)"),
          ("violation_reason", "Regex sau “do / vì / vi phạm …”\nngắt ranh giới dấu chấm câu"),
          ("coordinated_items", "Token Delimiter (re.split)\nphân rã danh sách, ghép cặp 1-1")]),
        (69, "Điều hành", "CHI_DAO · CHU_TRI\nPHOI_HOP · LAM_VIEC_VOI",
         [("action_content", ""),
          ("· CHI_DAO", "Positional Entity Masking <ORG>\nRegex Trimming loại đại từ, trợ từ"),
          ("· CHU_TRI, LAM_VIEC", "Regex bóc tên hội nghị, buổi làm việc"),
          ("· PHOI_HOP", "Regex mệnh đề nội dung phối hợp")]),
    ]
    for x, title, types, items in cols:
        cx = x + 15.5
        arrow(ax, 50, 64, cx, 58.7)
        box(ax, x, 52, 31, 6.5, "", fc=BLUE_DK, ec=BLUE_DK, round_=0.8)
        ax.text(cx, 55.25, title, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold", zorder=4)
        box(ax, x, 12, 31, 40, "", fc="white", ec=BLUE, round_=0.8)
        ax.text(cx, 50.3, types, ha="center", va="top", fontsize=7, color=MUTED, linespacing=1.3, zorder=4)
        y = 43.3
        for k, d in items:
            ax.text(x + 1.6, y, k, ha="left", va="top", fontsize=7.5, color=BLUE_DK, fontweight="bold", zorder=4)
            y -= 2.5
            if d:
                ax.text(x + 1.6, y, d, ha="left", va="top", fontsize=7.2, color=INK, linespacing=1.25, zorder=4)
                y -= 2.4 * (d.count("\n") + 1)
            y -= 1.6
        arrow(ax, cx, 12, 50, 7.2)
    box(ax, 20, 0.2, 60, 7, "ĐẦU RA: Bản ghi tham số sự kiện N-ngôi nạp Neo4j (Tốc độ 12.671 câu/s)", fs=8.2, fc=GREY_BG, ec=LINE)
    save(fig, "hinh3_luong_trich_xuat.png")


# ---------------------------------------------------------------------------
# Hình 4. Ví dụ từng bước: action_content
# ---------------------------------------------------------------------------
def fig4():
    fig, ax = canvas(7.2, 5.0, 100, 72)
    ax.set_ylim(-4, 68)
    steps = [
        ("Câu nguồn gốc",
         "Chỉ đạo một số nhiệm vụ cụ thể, Thủ tướng yêu cầu Bộ Xây dựng tiếp tục nghiên cứu, rà soát,\n"
         "hoàn thiện các văn bản quy phạm pháp luật để tháo gỡ khó khăn, vướng mắc phát sinh trong thực tiễn, …",
         GREY_BG, LINE),
        ("Thao tác 1. Cắt sau từ kích hoạt chỉ đạo bằng Regex: re.search(r'\\b(?:yêu cầu|chỉ đạo|giao)\\b\\s*(.+)', ...)",
         "Bộ Xây dựng tiếp tục nghiên cứu, rà soát, hoàn thiện các văn bản quy phạm pháp luật để tháo gỡ …",
         "white", LINE),
        ("Thao tác 2. Positional Masking che <TARGET> và Regex Strip loại bỏ trợ từ đệm ('Bộ Xây dựng tiếp tục')",
         "nghiên cứu, rà soát, hoàn thiện các văn bản quy phạm pháp luật để tháo gỡ …",
         "white", LINE),
        ("Thao tác 3. Tách vị ngữ hành động bằng mẫu ngắt ranh giới cú pháp: re.split(r'[;\\.]|\\bđồng thời\\b|\\bnhằm\\b|\\bđể\\b')",
         "nghiên cứu, rà soát, hoàn thiện các văn bản quy phạm pháp luật",
         BLUE_BG, BLUE),
    ]
    y = 67
    for i, (title, text, fc, ec) in enumerate(steps):
        h = 12.0 if i == 0 else 9.0
        y -= h
        box(ax, 0, y, 100, h, "", fc=fc, ec=ec, round_=0.8)
        ax.text(1.6, y + h - 2.2, title, fontsize=7.6, fontweight="bold", color=BLUE_DK if i else INK2, va="center")
        ax.text(1.6, y + (h - 4) / 2 + 0.2, text, fontsize=7.9, color=INK, va="center", linespacing=1.35,
                fontweight="bold" if i == 3 else "normal")
        if i < 3:
            arrow(ax, 50, y, 50, y - 3.2)
        y -= 3.4
    # So sánh với hệ cơ sở
    y -= 2.0
    ax.text(0, y, "Đầu ra của hệ cơ sở (underthesea chunking cú pháp):",
            fontsize=7.8, color=INK2, fontweight="bold", va="center")
    box(ax, 0, y - 11.6, 100, 9.4,
        "một số nhiệm vụ cụ thể , Thủ tướng yêu cầu Bộ Xây dựng tiếp tục nghiên cứu , rà soát ,\n"
        "hoàn thiện các văn bản quy phạm pháp luật",
        fs=7.9, fc=BAD_BG, ec=BAD, color=INK)
    ax.text(0, y - 14.6, "→ underthesea chunking lẫn cả trạng ngữ mở đầu, chủ thể, từ kích hoạt và cơ quan nhận lệnh (chỉ 35% dùng được).",
            fontsize=7.5, color=BAD, va="center")
    save(fig, "hinh4_vi_du_action_content.png")


# ---------------------------------------------------------------------------
# Hình 5. Hai cạm bẫy và Giải pháp Partitioned Record Linkage v2
# ---------------------------------------------------------------------------
def fig5():
    fig, ax = canvas(7.2, 9.2, 100, 132)

    def parts(y, kind, prefix, core, core_fc):
        box(ax, 20, y, 8, 5.4, kind, fs=7.6, fc=GREY_BG, ec=LINE, round_=0.5)
        box(ax, 29, y, 37, 5.4, prefix, fs=7.6, fc="white", ec=LINE, round_=0.5)
        box(ax, 67, y, 15, 5.4, core, fs=7.6, bold=True, fc=core_fc, ec=LINE, round_=0.5)

    def header(y):
        for x, w, t in ((20, 8, "Loại"), (29, 37, "Tiền tố (loại hình cơ quan)"), (67, 15, "Tên lõi")):
            ax.text(x + w / 2, y, t, ha="center", fontsize=7.2, color=MUTED)

    # ---- (a)
    ax.text(0, 128.5, "(a) Bẫy trùng tiền tố — So khớp mờ chuỗi (RapidFuzz / Token Set Ratio)",
            fontsize=8.6, fontweight="bold")
    header(122.8)
    ax.text(0, 118.2, "UBND TP Hà Nội", fontsize=8, va="center")
    parts(115.5, "org", "uy_ban_nhan_dan_thanh_pho", "ha_noi", YEL_BG)
    ax.text(0, 111.2, "UBND TP Cần Thơ", fontsize=8, va="center")
    parts(108.5, "org", "uy_ban_nhan_dan_thanh_pho", "can_tho", YEL_BG)
    box(ax, 0, 93.5, 48.5, 11.5,
        "So khớp mờ RapidFuzz Token Set Ratio\nđộ tương đồng = 90,4  ≥  ngưỡng 85\n→ GỘP NHẦM TAI HẠI (Lỗi 100%)",
        fs=7.8, fc=BAD_BG, ec=BAD)
    box(ax, 51.5, 93.5, 48.5, 11.5,
        "Luật phân rã đặc trưng: so tên lõi trước\nha_noi  ≠  can_tho\n→ CHẶN ĐÚNG TUYỆT ĐỐI",
        fs=7.8, fc=GOOD_BG, ec=GOOD)
    ax.text(84, 118.2, "tên lõi khác nhau", fontsize=7.4, color=INK2, va="center")
    ax.text(84, 111.2, "tiền tố giống hệt", fontsize=7.4, color=INK2, va="center")
    ax.plot([0, 100], [89.5, 89.5], color=GRID, lw=1)

    # ---- (b)
    ax.text(0, 85, "(b) Bẫy cùng địa phương — So khớp tiền tố bằng tập con (Subset Trap)",
            fontsize=8.6, fontweight="bold")
    header(79.3)
    ax.text(0, 74.7, "Tỉnh ủy Đồng Nai", fontsize=8, va="center")
    parts(72, "org", "tinh_uy", "dong_nai", YEL_BG)
    ax.text(0, 67.7, "UBND tỉnh Đồng Nai", fontsize=8, va="center")
    parts(65, "org", "uy_ban_nhan_dan_tinh", "dong_nai", YEL_BG)
    ax.text(84, 74.7, "tên lõi trùng nhau", fontsize=7.4, color=INK2, va="center")
    ax.text(84, 67.7, "tiền tố khác nhau", fontsize=7.4, color=INK2, va="center")
    box(ax, 0, 48, 100, 13.5,
        "Luật ngây thơ: tên lõi trùng → so tiền tố bằng token_set_ratio với ngưỡng 80\n"
        "{tinh, uy}  là tập con của  {uy, ban, nhan, dan, tinh}   →   độ tương đồng = 100\n"
        "→ GỘP NHẦM Tỉnh ủy với Ủy ban nhân dân tỉnh (sai 98/108 cặp)",
        fs=7.8, fc=BAD_BG, ec=BAD)
    ax.plot([0, 100], [44.0, 44.0], color=GRID, lw=1)

    # ---- (c)
    ax.text(0, 39.5, "(c) Giải pháp hoàn thiện: Thuật toán Partitioned Record Linkage v2 (Đạt độ chính xác 100%)",
            fontsize=8.6, fontweight="bold", color=GOOD)
    box(ax, 0, 12, 100, 24.5, "", fc=GOOD_BG, ec=GOOD, lw=1.2)
    ax.text(2, 33.5, "NGUYÊN TẮC HOẠT ĐỘNG CỦA THUẬT TOÁN:", fontsize=7.8, fontweight="bold", color=GOOD)
    lines_c = [
        "1. Phân rã 3 thành phần: Entity Slug = (Kind, Prefix_Context, Core_Name).",
        "2. Chặn thể chế cứng (Hard Institutional Blocking): Cơ quan Đảng (tinh_uy) ≠ Chính quyền (ubnd) → KHÔNG BAO GIỜ GỘP.",
        "3. So khớp Tên lõi địa phương: ha_noi ≠ can_tho → Giữ nguyên tách biệt (triệt tiêu 100% bẫy (a)).",
        "4. Bảng ánh xạ bí danh chính tắc (config/org_aliases.json): tp_hcm → tp_ho_chi_minh, so_kh_va_dt → so_ke_hoach_va_dau_tu.",
        "5. Kết quả kiểm định trên 8.937 cạnh: Độ chính xác 100.0% (0 lỗi gộp sai), rút gọn còn 4.583 cạnh trong 0,117 giây."
    ]
    cy = 29.5
    for l in lines_c:
        ax.text(3, cy, l, fontsize=7.4, color=INK, va="center")
        cy -= 4.2

    ax.text(0, 4, "Thuật toán Partitioned Record Linkage v2 thay thế hoàn toàn so khớp mờ ngây thơ, giải quyết triệt để cả hai bẫy (a) và (b).",
            fontsize=7.5, color=INK2, va="center", fontweight="bold")
    save(fig, "hinh5_hai_bay_khu_trung.png")


# ---------------------------------------------------------------------------
# Hình 6. F1 (khớp mềm) theo từng trường
# ---------------------------------------------------------------------------
def fig6():
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    fields = ["Số hiệu VB\n(legal_doc)", "Thời hạn\n(deadline)", "Mức độ khẩn\n(urgency)",
              "Hình thức\n(appoint_type)", "Hình thức KL\n(penalty_form)", "Chức vụ\n(role)"]
    f1_base = [99.7, 95.8, 86.4, 100.0, 99.4, 99.4]
    f1_opt  = [99.4, 100.0, 100.0, 100.0, 97.8, 97.2]
    import numpy as np
    x = np.arange(len(fields))
    w = 0.36
    ax.bar(x - w / 2, f1_base, w, label="Hệ cơ sở (underthesea chunker)", color=BLUE, zorder=3)
    ax.bar(x + w / 2, f1_opt,  w, label="ViGov-IE v2 (Động cơ luật chuyên sâu)", color=ORANGE, zorder=3)
    for i in range(len(fields)):
        ax.text(x[i] - w / 2, f1_base[i] + 0.8, f"{f1_base[i]:.1f}%", ha="center", fontsize=7.2, color=INK2)
        ax.text(x[i] + w / 2, f1_opt[i] + 0.8,  f"{f1_opt[i]:.1f}%",  ha="center", fontsize=7.2, color=INK, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(fields, fontsize=7.6)
    ax.set_ylim(75, 105)
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
    fig, ax = plt.subplots(figsize=(6.2, 2.7))
    cats = ["Sạch, dùng được ngay", "Dùng được (dính tiền tố)", "Bị cụt / thiếu", "Lẫn chủ thể / sai"]
    base_vals = [6, 8, 17, 9]     # 14 / 40 dùng được (35.0%)
    opt_vals  = [29, 10, 0, 1]    # 39 / 40 dùng được (97.5%)
    import numpy as np
    x = np.arange(len(cats))
    w = 0.36
    ax.bar(x - w / 2, base_vals, w, label="Hệ cơ sở (underthesea chunker)", color=BLUE, zorder=3)
    ax.bar(x + w / 2, opt_vals,  w, label="ViGov-IE v2 (Positional Masking)", color=ORANGE, zorder=3)
    for i in range(len(cats)):
        ax.text(x[i] - w / 2, base_vals[i] + 0.6, str(base_vals[i]), ha="center", fontsize=7.6, color=INK2)
        ax.text(x[i] + w / 2, opt_vals[i] + 0.6,  str(opt_vals[i]),  ha="center", fontsize=7.6, color=INK, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=7.5)
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
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.8, 2.7), gridspec_kw={"width_ratios": [1.05, 1], "wspace": 0.5})
    labels = ["Cạnh thô", "Gộp trùng khớp\nchính xác", "Partitioned\nRecord Linkage"]
    vals = [8937, 4758, 4583]
    a.bar(range(3), vals, width=0.52, color=[GREY_FILL, BLUE, GOOD], zorder=3)
    for i, v in enumerate(vals):
        a.text(i, v + 180, f"{v:,}".replace(",", "."), ha="center", fontsize=8.4, color=INK, fontweight="bold" if i == 2 else "normal")
    a.set_xticks(range(3))
    a.set_xticklabels(labels, fontsize=7.8)
    a.set_ylim(0, 10400)
    a.set_yticks([0, 2500, 5000, 7500, 10000])
    a.set_yticklabels(["0", "2.500", "5.000", "7.500", "10.000"], fontsize=7.6)
    a.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    a.set_title("(a) Số cạnh tin tức sau mỗi bước", fontsize=8.6, loc="left", color=INK, pad=8)
    
    cats = [("Chính xác: Hợp nhất an toàn (0 lỗi sai)", 4354, GOOD, "white"),
            ("Chặn đúng: Hai cơ quan khác địa phương", 1422, BLUE_LT, INK),
            ("Chặn đúng: Đảng ≠ Chính quyền cùng tỉnh", 98, BLUE_DK, "white")]
    for i, (name, v, c, tc) in enumerate(cats):
        y = 2 - i
        b.barh(y, v, height=0.5, color=c, zorder=3)
        b.text(v + 80, y, str(v), va="center", fontsize=8.2, color=INK, fontweight="bold")
        b.text(0, y + 0.42, name, va="center", fontsize=7.5, color=INK2)
    b.set_xlim(0, 5200)
    b.set_ylim(-0.5, 2.9)
    b.set_yticks([])
    b.set_xticks([0, 1000, 2500, 4000, 5000])
    b.tick_params(axis="x", labelsize=7.4)
    b.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    b.set_title("(b) Kiểm định thuật toán Partitioned Linkage", fontsize=8.6, loc="left", color=INK, pad=8)
    for ax in (a, b):
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(GREY_FILL)
        ax.tick_params(axis="both", length=0, colors=INK2)
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
