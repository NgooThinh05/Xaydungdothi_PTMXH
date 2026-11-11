# -*- coding: utf-8 -*-
"""
Dựng báo cáo nghiên cứu ViGov-IE (bản đã kiểm định) ra DOCX.

  python report/generate_paper_figures.py   # sinh hình vào report/figures_paper/
  python report/build_paper_docx.py         # sinh report/Bao_Cao_ViGov_IE_Kiem_Dinh.docx

Mọi số liệu trong báo cáo lấy từ scratch/verify_claims.py và scratch/verify_dedup.py
(kết quả lưu ở report/verified_metrics.json).
"""
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "report" / "figures_paper"
OUT = ROOT / "report" / "Bao_Cao_ViGov_IE_Kiem_Dinh.docx"

FONT = "Times New Roman"
MONO = "Consolas"
BLACK = RGBColor(0, 0, 0)
GREY = RGBColor(0x44, 0x44, 0x44)

doc = Document()


# ------------------------------------------------------------------ tiện ích
def set_font(run, name=FONT, size=None, bold=None, italic=None, color=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color


TOKEN = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)")


def add_runs(p, text, size=12, bold=False, italic=False, color=None):
    """Hỗ trợ **đậm**, *nghiêng*, `mã`."""
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**"):
            set_font(p.add_run(part[2:-2]), size=size, bold=True, italic=italic, color=color)
        elif part.startswith("`"):
            set_font(p.add_run(part[1:-1]), name=MONO, size=size - 1.5, bold=bold, color=color)
        elif part.startswith("*"):
            set_font(p.add_run(part[1:-1]), size=size, bold=bold, italic=True, color=color)
        else:
            set_font(p.add_run(part), size=size, bold=bold, italic=italic, color=color)


def para(text, size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=6, indent=True,
         bold=False, italic=False, color=None, keep=False, line=1.15):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if indent:
        pf.first_line_indent = Cm(0.75)
    if keep:
        pf.keep_with_next = True
    add_runs(p, text, size=size, bold=bold, italic=italic, color=color)
    return p


def heading(text, level=1):
    p = doc.add_heading(level=level)
    pf = p.paragraph_format
    pf.space_before = Pt(14 if level == 1 else 10)
    pf.space_after = Pt(6 if level == 1 else 4)
    pf.keep_with_next = True
    set_font(p.add_run(text), size=13 if level == 1 else 12, bold=True, italic=(level == 3), color=BLACK)
    return p


def bullets(items, numbered=False, size=12):
    for i, t in enumerate(items, 1):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Cm(1.25)
        pf.first_line_indent = Cm(-0.6)
        pf.space_after = Pt(3)
        pf.line_spacing = 1.15
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        set_font(p.add_run((f"{i}." if numbered else "•") + "\t"), size=size)
        add_runs(p, t, size=size)
        tabs = p._element.get_or_add_pPr()
        t_el = OxmlElement("w:tabs")
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "left")
        tab.set(qn("w:pos"), str(int(Cm(1.25).twips)))
        t_el.append(tab)
        tabs.append(t_el)
    doc.paragraphs[-1].paragraph_format.space_after = Pt(6)


def _border(cell, **kw):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders")
        tcPr.append(b)
    for edge in ("top", "left", "bottom", "right"):
        el = b.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            b.append(el)
        sz = kw.get(edge)
        if sz:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(sz))
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), "000000")
        else:
            el.set(qn("w:val"), "nil")


def _shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def caption(text, above=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.space_before = Pt(8 if above else 4)
    pf.space_after = Pt(4 if above else 12)
    pf.keep_with_next = above
    label, _, rest = text.partition(".")
    set_font(p.add_run(label + "."), size=10.5, bold=True)
    add_runs(p, rest, size=10.5)
    return p


def table(title, headers, rows, widths, align=None, size=9.5, bold_last=False, note=None,
          group_header=None):
    """Bảng kiểu booktabs: kẻ ngang trên, dưới tiêu đề và cuối bảng; không kẻ dọc."""
    caption(title, above=True)
    n_head = 2 if group_header else 1
    t = doc.add_table(rows=len(rows) + n_head, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    align = align or ["l"] + ["c"] * (len(headers) - 1)
    amap = {"l": WD_ALIGN_PARAGRAPH.LEFT, "c": WD_ALIGN_PARAGRAPH.CENTER, "r": WD_ALIGN_PARAGRAPH.RIGHT}

    def fill(cell, text, a, bold=False, top=None, bottom=None):
        cell.width = Cm(1)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.paragraph_format.alignment = amap[a]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.0
        add_runs(p, text, size=size, bold=bold)
        _border(cell, top=top, bottom=bottom)

    r0 = 0
    if group_header:
        # group_header: list of (text, span)
        col = 0
        for text, span in group_header:
            c = t.cell(0, col)
            if span > 1:
                c = c.merge(t.cell(0, col + span - 1))
            fill(c, text, "c", bold=True, top=12, bottom=4 if text else None)
            col += span
        r0 = 1
    for j, h in enumerate(headers):
        fill(t.cell(r0, j), h, "c" if j else "l", bold=True, top=None if group_header else 12, bottom=6)
    for i, row in enumerate(rows):
        last = i == len(rows) - 1
        for j, v in enumerate(row):
            fill(t.cell(i + n_head, j), str(v), align[j], bold=(bold_last and last),
                 top=4 if (bold_last and last) else None, bottom=12 if last else None)
    for ri, row in enumerate(t.rows):
        for j, c in enumerate(row.cells):
            c.width = Cm(widths[j])
            if ri < len(t.rows) - 1:      # giữ cả bảng trên một trang
                for cp in c.paragraphs:
                    cp.paragraph_format.keep_with_next = True
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
    if note:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(10)
        p.paragraph_format.line_spacing = 1.0
        add_runs(p, note, size=9.5, italic=True, color=GREY)
    else:
        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(4)
        sp.paragraph_format.line_spacing = 0.6
    return t


def figure(name, text, width=13.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.left_indent = Cm(0)
    pf.right_indent = Cm(0)
    pf.first_line_indent = Cm(0)
    pf.space_before = Pt(8)
    pf.space_after = Pt(2)
    pf.keep_with_next = True
    p.add_run().add_picture(str(FIG / name), width=Cm(width))
    caption(text, above=False)


def example(label, text):
    """Khối ví dụ thụt lề, chữ nhỏ."""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(1.0)
    pf.right_indent = Cm(0.5)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.1
    set_font(p.add_run(label + " "), size=10.5, bold=True)
    add_runs(p, text, size=10.5)
    return p


# ------------------------------------------------------------------ trang, kiểu
sec = doc.sections[0]
sec.orientation = WD_ORIENT.PORTRAIT
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = Cm(3.0)
sec.right_margin = Cm(2.0)
sec.top_margin = sec.bottom_margin = Cm(2.5)

st = doc.styles["Normal"]
st.font.name = FONT
st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
for lv in (1, 2, 3):
    hs = doc.styles[f"Heading {lv}"]
    hs.font.name = FONT
    hs.font.color.rgb = BLACK
    hs.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    hs.element.rPr.rFonts.set(qn("w:ascii"), FONT)
    hs.element.rPr.rFonts.set(qn("w:hAnsi"), FONT)

# số trang ở chân trang
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run()
for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if tag:
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), tag)
    else:
        el = OxmlElement("w:instrText")
        el.set(qn("xml:space"), "preserve")
        el.text = txt
    r._r.append(el)
set_font(r, size=10)

# ================================================================== TIÊU ĐỀ
para("ViGov-IE: TRÍCH XUẤT THAM SỐ SỰ KIỆN N-NGÔI BẰNG LUẬT CÚ PHÁP CHO ĐỒ THỊ TRI THỨC QUẢN LÝ NHÀ NƯỚC VIỆT NAM",
     size=15, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, bold=True, after=6, line=1.2)
para("ViGov-IE: Rule-based N-ary Event Argument Extraction for a Vietnamese Governance Knowledge Graph",
     size=12, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, italic=True, after=10)
para("Nhóm thực hiện Đề tài 19", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=0)
para("Học phần Phân tích Mạng xã hội — tháng 11 năm 2026", size=11, align=WD_ALIGN_PARAGRAPH.CENTER,
     indent=False, after=14, color=GREY)

# ------------------------------------------------------------------ Tóm tắt
p = para("", size=11, indent=False, after=6, line=1.12)
p.paragraph_format.left_indent = Cm(0.75)
p.paragraph_format.right_indent = Cm(0.75)
add_runs(p, "**Tóm tắt.** Tin thời sự – nội chính tiếng Việt chứa nhiều sự kiện quản lý nhà nước như bổ nhiệm, điều động, "
            "kỷ luật, chỉ đạo. Biểu diễn mỗi sự kiện bằng một cạnh giữa hai thực thể làm mất các chi tiết quan trọng: "
            "số quyết định, chức vụ được giao, hình thức kỷ luật, nội dung chỉ đạo. Bài báo mô tả ViGov-IE, bộ trích xuất "
            "dựa hoàn toàn trên luật, biến mỗi sự kiện thành một nút đồ thị mang tối đa chín tham số, và trình bày một "
            "đợt kiểm định độc lập các kết quả của hệ thống. Trên 446 câu có nhãn tham chiếu sinh tự động, phiên bản 2 "
            "tăng độ phủ khớp mềm từ 94,2% lên 96,2% nhưng độ chính xác giảm từ 99,8% xuống 87,1%, kéo F1 gộp từ 96,9% "
            "xuống 91,4%. Vì nhãn tham chiếu chính là đầu ra của hệ cơ sở, phép so này thiên về hệ cơ sở; chúng tôi do đó "
            "rà soát thủ công 40 câu chỉ đạo lấy ngẫu nhiên: phiên bản 2 cho nội dung chỉ đạo dùng được ở 29 câu so với "
            "14 câu của hệ cơ sở, và số câu bị lẫn chủ thể vào nội dung giảm từ 8 xuống 1. Phiên bản 2 không cần bộ phân "
            "cụm cú pháp nên nhanh hơn hệ cơ sở từ 31 đến 79 lần trên CPU. Với bài toán khử trùng thực thể, luật phân rã "
            "định danh chặn được 1.422 trong 1.447 cặp dễ bị gộp nhầm do trùng tiền tố, nhưng 98 trong 108 cặp mà luật "
            "gộp thêm lại là hai cơ quan khác nhau ở cùng địa phương. Bài báo nêu rõ nguyên nhân của từng lỗi và các "
            "phần của thiết kế chưa được cài đặt.", size=11)
p = para("", size=11, indent=False, after=12)
p.paragraph_format.left_indent = Cm(0.75)
p.paragraph_format.right_indent = Cm(0.75)
add_runs(p, "**Từ khóa:** trích xuất sự kiện, tham số sự kiện, đồ thị tri thức, khử trùng thực thể, hệ luật, "
            "xử lý tiếng Việt, văn bản hành chính.", size=11)

# ================================================================== 1
heading("1. Giới thiệu")
para("Đồ thị tri thức về bộ máy nhà nước cho phép trả lời những câu hỏi mà tìm kiếm văn bản khó đáp ứng: ai bổ nhiệm ai, "
     "theo quyết định nào, vào chức vụ gì; cơ quan nào bị kỷ luật và với hình thức nào; một bộ được giao làm việc gì và "
     "hạn đến khi nào. Nguồn tin cho các câu hỏi này nằm trong báo chí thời sự – nội chính, nơi mỗi câu văn thường gói "
     "một sự kiện cùng nhiều chi tiết đi kèm.")
para("Cách biểu diễn phổ biến là quan hệ nhị phân: một cạnh có nhãn nối hai thực thể, ví dụ *Thủ tướng –BO_NHIEM→ "
     "Nguyễn Hải Trung*. Cạnh này giữ được ai tác động đến ai nhưng bỏ mất số quyết định, chức vụ mới và hình thức bổ "
     "nhiệm. Đề tài 19 đã xây một đồ thị gồm 8.581 nút thực thể và 18.189 cạnh từ Wikipedia tiếng Việt và báo chí; "
     "bài báo này tập trung vào bước tiếp theo, là lấy lại các chi tiết bị mất đó dưới dạng *tham số sự kiện*.")
para("Chúng tôi chọn hướng tiếp cận bằng luật thay vì mô hình học sâu vì ba lý do: không có dữ liệu gán nhãn tay cho miền "
     "này; văn phong hành chính có khuôn mẫu ổn định; và hệ thống cần chạy được trên máy tính cá nhân. Lựa chọn này có "
     "cái giá của nó, và phần lớn bài báo dành để đo cái giá đó một cách trung thực.")
para("Đóng góp của bài báo gồm:", after=3)
bullets([
    "Mô hình sự kiện N-ngôi cho mười loại sự kiện quản lý nhà nước với chín tham số, và bộ trích xuất ViGov-IE phiên bản 2 cài đặt mô hình đó bằng luật (Mục 4).",
    "Một luật khử trùng thực thể dựa trên phân rã định danh thành *loại – tiền tố – tên lõi*, cùng phân tích cho thấy luật này giải được bẫy trùng tiền tố nhưng mắc một bẫy khác (Mục 5).",
    "Một đợt kiểm định độc lập: đo lại toàn bộ số liệu, chỉ ra rằng nhãn tham chiếu của bộ đánh giá là đầu ra của hệ cơ sở, và bổ sung một phép rà soát thủ công không phụ thuộc vào nhãn đó (Mục 6 và 7).",
    "Danh sách cụ thể các lỗi đã tìm thấy trong phiên bản 2 và các thành phần mới dừng ở mức thiết kế (Mục 8).",
], numbered=True)

# ================================================================== 2
heading("2. Công trình liên quan")
para("**Trích xuất sự kiện tiếng Việt.** BKEE [1] là bộ dữ liệu trích xuất sự kiện đầu tiên dành riêng cho tiếng Việt, "
     "gồm 1.066 văn bản gán nhãn tay với hơn 33 loại sự kiện và 28 vai tham số, kèm các mô hình cơ sở cho ba bài toán "
     "phát hiện đề cập sự kiện, phát hiện sự kiện và trích xuất tham số. Lược đồ của BKEE theo truyền thống ACE [7] và "
     "phủ miền tổng quát; các tham số đặc thù của văn bản hành chính như số hiệu văn bản hay hình thức kỷ luật không "
     "nằm trong lược đồ đó.")
para("**Trích xuất thông tin mở và quan hệ.** vnOIE [2] trích các bộ ba từ câu tiếng Việt dựa trên mệnh đề và phân tích "
     "phụ thuộc, không cần lược đồ định trước; các tác giả báo cáo độ chính xác 83,71%. Do không chuẩn hóa vai, đầu ra "
     "của trích xuất mở khó nạp thẳng vào một đồ thị có lược đồ. Bài toán chia sẻ VLSP RelEx 2020 [3] phân loại cặp "
     "thực thể trong tin tức vào bốn loại quan hệ định trước, trên 1.056 văn bản với 5.900 thể hiện quan hệ. Cả hai "
     "hướng đều dừng ở quan hệ hai ngôi.")
para("**Khử trùng thực thể.** Liên kết bản ghi là bài toán kinh điển [5]; kỹ thuật *blocking* chia bản ghi thành các khối "
     "để chỉ so sánh trong cùng khối. Luật phân rã ở Mục 5 là một dạng blocking theo tên lõi áp dụng cho định danh cơ "
     "quan Việt Nam.")
para("Bảng 1 đặt ViGov-IE cạnh các công trình trên. Các hệ thống giải những bài toán khác nhau trên dữ liệu khác nhau, "
     "nên bảng chỉ so sánh về phạm vi và phương pháp; chúng tôi không so sánh điểm số giữa các hệ.")
table("Bảng 1. So sánh định tính ViGov-IE với các công trình liên quan",
      ["Công trình", "Bài toán", "Lược đồ", "Phương pháp", "Dữ liệu đánh giá"],
      [["BKEE [1]", "Trích xuất sự kiện miền tổng quát", "Hơn 33 loại sự kiện, 28 vai tham số", "Mô hình học có giám sát", "1.066 văn bản gán nhãn tay"],
       ["vnOIE [2]", "Trích xuất thông tin mở", "Không có lược đồ", "Mệnh đề + phân tích phụ thuộc", "Câu tin tức, chấm tay"],
       ["VLSP RelEx [3]", "Phân loại quan hệ hai ngôi", "4 loại quan hệ", "Các hệ dự thi (đa số học sâu)", "1.056 văn bản, 5.900 quan hệ"],
       ["ViGov-IE (bài này)", "Tham số sự kiện quản lý nhà nước", "10 loại sự kiện, 9 tham số", "Luật theo khuôn mẫu cú pháp", "446 câu nhãn tự động; 40 câu rà soát tay"]],
      widths=[2.9, 3.3, 3.2, 3.3, 3.3], align=["l", "l", "l", "l", "l"], size=9.5)

# ================================================================== 3
heading("3. Dữ liệu và mô hình sự kiện")
heading("3.1. Đồ thị nền", level=2)
para("Đồ thị nền được dựng từ hai nguồn. Wikipedia tiếng Việt cung cấp các quan hệ cấu trúc tương đối ổn định (giữ chức "
     "vụ, trực thuộc, kế nhiệm). Báo chí thời sự – nội chính cung cấp các sự kiện diễn ra theo thời gian. Bảng 2 tóm "
     "tắt quy mô; mọi con số về đồ thị đều được đếm lại trực tiếp từ các tệp trong `data/processed/graph/`.")
table("Bảng 2. Quy mô dữ liệu và đồ thị",
      ["Thành phần", "Số lượng", "Ghi chú"],
      [["Bài báo thu thập", "16.757", "Theo thống kê giai đoạn thu thập†"],
       ["Trang Wikipedia", "3.134", "Theo thống kê giai đoạn thu thập†"],
       ["Nút Người", "5.438", "Chính khách, lãnh đạo cơ quan"],
       ["Nút Cơ quan", "1.516", "Cơ quan Đảng, nhà nước, sở, ngành"],
       ["Nút Chức vụ", "1.563", "Một vị trí gắn với một cơ quan"],
       ["Nút Tỉnh/Thành", "64", ""],
       ["Nút Sự kiện", "6.694", "Mỗi nút giữ câu bằng chứng và URL nguồn"],
       ["Cạnh cơ sở", "18.189", "19 loại quan hệ"],
       ["Cạnh nối sự kiện", "13.388", "Hai cạnh cho mỗi sự kiện: chủ thể và đối tượng"]],
      widths=[4.2, 2.4, 8.4], align=["l", "r", "l"],
      note="† Dữ liệu thô không nằm trong kho mã nên hai con số này không được đếm lại trong đợt kiểm định.")

heading("3.2. Sự kiện N-ngôi", level=2)
para("Thay cho một cạnh, mỗi sự kiện được biểu diễn bằng một nút riêng. Nút sự kiện nối với chủ thể (bên ra quyết định, "
     "chỉ đạo) và đối tượng (bên chịu tác động), và mang các tham số mô tả chính sự kiện đó. Hình 1 minh họa sự khác "
     "biệt trên một câu thật trong ngữ liệu.")
figure("hinh2_su_kien_n_ngoi.png",
       "Hình 1. Cùng một câu nguồn dưới hai cách biểu diễn. (a) Cạnh nhị phân chỉ giữ được hai thực thể và loại quan hệ. "
       "(b) Nút sự kiện giữ thêm số quyết định, hình thức bổ nhiệm, chức vụ mới và ngày hiệu lực.", width=13.5)
para("Hệ thống phân biệt mười loại sự kiện (Bảng 3) và chín tham số (Bảng 4). Loại sự kiện do bước trích quan hệ ở "
     "thượng nguồn xác định qua từ kích hoạt; ViGov-IE nhận câu cùng loại sự kiện và chỉ lo phần tham số.")
table("Bảng 3. Mười loại sự kiện: số nút trong đồ thị và số câu trong bộ đánh giá",
      ["Loại sự kiện", "Ý nghĩa", "Số nút sự kiện", "Số câu đánh giá"],
      [["CHI_DAO", "Chỉ đạo, yêu cầu, giao nhiệm vụ", "2.358", "92"],
       ["PHOI_HOP", "Phối hợp công tác", "1.599", "41"],
       ["BO_NHIEM", "Bổ nhiệm, phê chuẩn, chỉ định", "1.065", "75"],
       ["CHU_TRI", "Chủ trì họp, hội nghị", "788", "44"],
       ["DIEU_DONG", "Điều động, luân chuyển", "381", "40"],
       ["KY_LUAT", "Thi hành kỷ luật", "249", "65"],
       ["LAM_VIEC_VOI", "Làm việc với địa phương, đơn vị", "109", "31"],
       ["MIEN_NHIEM", "Miễn nhiệm, cho thôi giữ chức", "99", "26"],
       ["KIEM_TRA", "Kiểm tra, giám sát", "39", "25"],
       ["THANH_TRA", "Thanh tra", "7", "7"],
       ["Tổng", "", "6.694", "446"]],
      widths=[3.2, 6.4, 2.8, 2.8], align=["l", "l", "r", "r"], bold_last=True)
table("Bảng 4. Chín tham số sự kiện",
      ["Tham số", "Nội dung", "Áp dụng cho", "Số sự kiện có giá trị"],
      [["`action_content`", "Việc được chỉ đạo; tên cuộc họp; nội dung phối hợp", "Chỉ đạo, chủ trì, phối hợp, làm việc", "2.368"],
       ["`appoint_type`", "Hình thức: bổ nhiệm mới, điều động, phê chuẩn, …", "Nhân sự", "1.453"],
       ["`role`", "Chức vụ được giao", "Nhân sự", "1.155"],
       ["`legal_doc`", "Số hiệu văn bản", "Mọi loại", "863"],
       ["`urgency`", "Từ chỉ mức độ khẩn (khẩn trương, kịp thời, …)", "Mọi loại", "857"],
       ["`tenure`", "Nhiệm kỳ hoặc thời hạn giữ chức", "Nhân sự", "649"],
       ["`deadline`", "Thời hạn hoàn thành", "Mọi loại", "233"],
       ["`penalty_form`", "Hình thức kỷ luật", "Kỷ luật", "176"],
       ["`violation_reason`", "Lý do, hành vi vi phạm", "Kỷ luật", "62"]],
      widths=[3.1, 6.2, 3.6, 2.6], align=["l", "l", "l", "r"],
      note="Cột cuối đếm trên 6.694 nút sự kiện hiện có trong đồ thị, do hệ cơ sở sinh ra.")

# ================================================================== 4
heading("4. Kiến trúc hệ thống")
heading("4.1. Tổng thể", level=2)
para("Hình 2 trình bày toàn bộ đường đi của dữ liệu, từ nguồn thô đến đồ thị. Hệ thống gồm bốn tầng nối tiếp; mỗi tầng "
     "nhận đầu ra của tầng trước và không cần biết tầng trước làm việc ra sao.")
figure("hinh1_kien_truc_tong_the.png",
       "Hình 2. Kiến trúc tổng thể. Khối viền xanh là phần xử lý ngôn ngữ; ViGov-IE là tầng 3. Đường đứt nét là các quan "
       "hệ cấu trúc đi thẳng từ Wikipedia vào đồ thị, không qua trích xuất sự kiện.", width=12.5)
para("**Tầng 1 – Thu thập.** Hai nguồn độc lập. Trang Wikipedia của chính khách và cơ quan được đọc qua infobox và liên "
     "kết; bài báo được lấy từ các chuyên mục thời sự, nội chính và lọc bỏ phần không phải nội dung.", indent=False, after=4)
para("**Tầng 2 – Tiền xử lý và liên kết thực thể.** Văn bản báo được chuẩn hóa Unicode và tách câu. Tên người, cơ quan, "
     "tỉnh thành trong câu được nhận diện và nối với mục tương ứng trong từ điển thực thể dựng từ Wikipedia. Từ kích "
     "hoạt như *bổ nhiệm*, *yêu cầu*, *kỷ luật* quyết định câu thuộc loại sự kiện nào. Kết quả của tầng này là 8.937 "
     "cạnh tin tức, mỗi cạnh kèm câu bằng chứng.", indent=False, after=4)
para("**Tầng 3 – Trích xuất tham số (ViGov-IE).** Với mỗi câu đã biết loại sự kiện, bộ trích xuất điền các tham số ở "
     "Bảng 4. Đây là trọng tâm của bài báo và được mô tả ở Mục 4.2.", indent=False, after=4)
para("**Tầng 4 – Hợp nhất và lưu trữ.** Mỗi sự kiện thành một nút mang tham số; các cạnh lặp lại giữa cùng một cặp thực "
     "thể được gộp (Mục 5). Đồ thị được nạp vào Neo4j để truy vấn bằng Cypher và hiển thị trên trình duyệt bằng Sigma.js.",
     indent=False)

heading("4.2. Bộ trích xuất tham số", level=2)
para("Bộ trích xuất là một hàm thuần: nhận câu, loại sự kiện và từ kích hoạt, trả về một bản ghi tham số. Nó không dùng "
     "mô hình học máy, không gọi bộ tách từ hay phân cụm cú pháp, chỉ dùng biểu thức chính quy và phép cắt chuỗi. "
     "Hình 3 cho thấy hai bước xử lý.")
figure("hinh3_luong_trich_xuat.png",
       "Hình 3. Luồng xử lý bên trong bộ trích xuất. Bước 1 chạy trên mọi câu. Bước 2 chọn một trong ba nhánh theo loại "
       "sự kiện; mỗi nhánh chỉ điền các tham số có nghĩa với loại sự kiện đó.", width=13.0)
para("**Bước 1 – Luật dùng chung.** Ba tham số có hình thức cố định nên trích được bằng mẫu, không phụ thuộc loại sự kiện. "
     "`legal_doc` khớp tên loại văn bản theo sau là số hiệu (*Quyết định số 397/QĐ-TTg*) hoặc số hiệu văn bản của Đảng "
     "(*148-QĐ/TW*). `deadline` khớp cụm chỉ hạn (*trước ngày*, *chậm nhất*, *trong quý*) theo sau là ngày, tháng, quý "
     "hoặc năm. `urgency` khớp một trong bảy từ chỉ mức độ khẩn. So với hệ cơ sở, phiên bản 2 nhận thêm các loại văn bản "
     "Nghị định, Thông tư, Công văn, số hiệu văn bản Đảng, và trích `deadline`, `urgency` cho mọi loại sự kiện thay vì "
     "chỉ cho sự kiện chỉ đạo.")
para("**Bước 2 – Nhánh nhân sự.** `appoint_type` được chọn từ một bảng 13 mẫu xếp theo thứ tự ưu tiên, mẫu cụ thể đứng "
     "trước mẫu chung (*bổ nhiệm lại* trước *bổ nhiệm*). `role` là đoạn văn bản đứng sau *giữ chức*, *làm*, *đảm nhiệm "
     "chức vụ*, dài tối đa 120 ký tự, cắt tại *nhiệm kỳ*, *thời hạn*, *kể từ*, *thay cho*, và bỏ phần sau chữ *nguyên* "
     "để không lấy nhầm chức vụ cũ. `tenure` khớp cụm nhiệm kỳ hoặc thời hạn.")
para("**Bước 2 – Nhánh kỷ luật.** `penalty_form` lấy hình thức cụ thể đầu tiên khớp được trong bảng bảy hình thức xếp từ "
     "nặng đến nhẹ, và không còn gán nhãn chung *Kỷ luật* khi câu không nêu hình thức. Khi một câu nêu nhiều người với "
     "nhiều hình thức khác nhau, câu được tách theo dấu phẩy, chấm phẩy và chữ *và*; mỗi vế có cả tên người lẫn hình "
     "thức tạo thành một cặp trong `coordinated_items`.")
para("**Bước 2 – Nhánh điều hành.** Với sự kiện chủ trì và làm việc, `action_content` là tên cuộc họp hay hội nghị. Với sự "
     "kiện phối hợp, đó là cụm đứng sau *phối hợp … tổ chức / triển khai / thực hiện / xây dựng*. Với sự kiện chỉ đạo, "
     "là loại nhiều nhất và khó nhất, luật gồm ba thao tác như ở Hình 4: cắt lấy phần sau từ kích hoạt, bỏ cơ quan nhận "
     "lệnh và các từ đệm đứng đầu, rồi ngắt tại ranh giới mệnh đề.")
figure("hinh4_vi_du_action_content.png",
       "Hình 4. Ba thao tác trích nội dung chỉ đạo trên một câu thật, và đầu ra của hệ cơ sở trên cùng câu đó. "
       "Khi không biết vị trí đối tượng, hệ cơ sở bắt đầu từ đầu câu và chỉ gỡ được chữ “Chỉ đạo” mở đầu, không tìm đến từ kích hoạt thật là “yêu cầu”.", width=13.5)
para("Điểm khác biệt chính so với hệ cơ sở nằm ở thao tác đầu: hệ cơ sở cần biết vị trí kết thúc của đối tượng trong câu "
     "để đặt mốc cắt, và khi không có thông tin này thì cắt sai chỗ; phiên bản 2 tự tìm từ kích hoạt trong câu. Thao tác "
     "thứ hai chỉ gỡ được cơ quan nhận lệnh khi theo sau nó là một từ đệm quen thuộc (*phải*, *cần*, *tiếp tục*, *khẩn "
     "trương*, …); Mục 7.2 cho thấy điều kiện này thường không thỏa.")

# ================================================================== 5
heading("5. Khử trùng thực thể bằng phân rã định danh")
para("Cùng một sự kiện thường được nhiều bài báo đưa tin, và cùng một cơ quan được viết theo nhiều cách. Trước khi nạp đồ "
     "thị, các cạnh nói về cùng một cặp thực thể và cùng loại quan hệ cần được gộp lại. Gộp theo định danh trùng khớp "
     "chính xác là an toàn nhưng bỏ sót các biến thể tên; so khớp mờ bắt được biến thể nhưng mắc một lỗi đặc thù của tên "
     "cơ quan Việt Nam.")
heading("5.1. Bẫy trùng tiền tố", level=2)
para("Tên cơ quan địa phương có dạng *loại hình cơ quan + địa danh*: Ủy ban nhân dân tỉnh X, Sở Y tế tỉnh X, Công an tỉnh "
     "X. Phần loại hình chiếm gần hết độ dài chuỗi và lặp lại ở mọi tỉnh, nên hai cơ quan cùng loại ở hai tỉnh khác nhau "
     "có độ tương đồng chuỗi rất cao. Đo bằng `token_set_ratio` của thư viện RapidFuzz [6] trên chuỗi định danh, UBND "
     "thành phố Hà Nội và UBND thành phố Cần Thơ giống nhau 90,4%; UBND tỉnh Bình Dương và Bình Phước giống nhau 91,4%. "
     "Trong 2.324 thực thể xuất hiện ở các cạnh tin tức, có 1.447 cặp thực thể khác nhau đạt từ 90% trở lên. Một ngưỡng "
     "so khớp mờ 90% sẽ coi tất cả các cặp này là một.")
heading("5.2. Luật phân rã", level=2)
para("Luật tách mỗi định danh thành ba phần: *loại* thực thể (người hay cơ quan), *tiền tố* chỉ loại hình cơ quan, và "
     "*tên lõi* là địa danh hoặc tên riêng. Hai thực thể chỉ được xét gộp khi cùng loại và cùng tên lõi (hoặc hai tên "
     "lõi là bí danh của cùng một tỉnh). Khi điều kiện này thỏa, hai tiền tố được so bằng `token_set_ratio` với ngưỡng "
     "80. Với người, tên lõi là họ tên, phần ngữ cảnh tỉnh đóng vai trò tiền tố.")
figure("hinh5_hai_bay_khu_trung.png",
       "Hình 5. Hai cái bẫy khi khử trùng. (a) Luật phân rã so tên lõi trước nên chặn đúng cặp cùng loại hình ở hai địa "
       "phương. (b) Khi tên lõi trùng, phép so tiền tố coi tập từ con là trùng khớp hoàn toàn, nên gộp nhầm hai cơ quan "
       "khác loại ở cùng địa phương.", width=13.0)
para("Hình 5 cho thấy luật xử lý đúng trường hợp nó được thiết kế cho, và đồng thời vì sao nó sai ở trường hợp ngược lại. "
     "`token_set_ratio` trả về 100 mỗi khi tập từ của chuỗi này nằm trọn trong tập từ của chuỗi kia. Tiền tố `tinh_uy` "
     "gồm hai từ *tinh* và *uy*, cả hai đều có trong `uy_ban_nhan_dan_tinh`; luật vì thế kết luận Tỉnh ủy và Ủy ban nhân "
     "dân của cùng một tỉnh là một thực thể. Kết quả định lượng nằm ở Mục 7.4.")

# ================================================================== 6
heading("6. Thiết lập thực nghiệm")
heading("6.1. Bộ đánh giá và nguồn gốc nhãn", level=2)
para("Bộ đánh giá gồm 446 câu lấy từ các nút sự kiện của đồ thị: 342 câu chọn ngẫu nhiên theo loại sự kiện (Bảng 3) và "
     "104 câu được chọn bằng mẫu để đại diện cho bốn hiện tượng khó (Mục 7.3). Mỗi câu có tối đa bảy trường nhãn tham "
     "chiếu; hai tham số `tenure` và `violation_reason` không được chấm.")
para("Nhãn tham chiếu **không phải do người gán**. Chúng được sinh tự động theo hai cách, và cả hai đều ảnh hưởng đến cách "
     "đọc kết quả:")
bullets([
    "Bốn trường `action_content`, `role`, `appoint_type`, `penalty_form` được chép từ giá trị đã lưu trên nút sự kiện, tức đầu ra của hệ cơ sở khi dựng đồ thị. Chúng tôi kiểm tra và thấy 368 trên 368 nhãn của bốn trường này trùng khớp từng ký tự với giá trị trong đồ thị. Hệ cơ sở vì vậy được chấm trên chính đầu ra của nó; mọi chỗ phiên bản 2 khác hệ cơ sở đều bị tính là sai, kể cả khi phiên bản 2 đúng hơn.",
    "Ba trường `legal_doc`, `deadline`, `urgency` được sinh bằng biểu thức chính quy gần như trùng với biểu thức của phiên bản 2. Điểm gần tuyệt đối của phiên bản 2 trên ba trường này phản ánh sự trùng lặp đó; phần có ý nghĩa là khoảng cách giữa hệ cơ sở và bộ mẫu rộng hơn.",
])
para("Vì vậy chúng tôi gọi đây là *nhãn tham chiếu* chứ không gọi là nhãn vàng, và coi điểm số trên bộ này là thước đo mức "
     "độ hai hệ **khác nhau**, chưa phải thước đo hệ nào **đúng**. Để có một phép đo không phụ thuộc vào nhãn tự động, "
     "Mục 7.2 bổ sung rà soát thủ công.")
heading("6.2. Các hệ được so sánh", level=2)
bullets([
    "**Hệ cơ sở** (`extraction/event_extractor.py`): luật kết hợp bộ phân cụm cú pháp của thư viện underthesea để tìm cụm động từ trong nội dung chỉ đạo.",
    "**ViGov-IE v2** (`extraction/vigov_ie_engine.py`): bộ trích xuất mô tả ở Mục 4.2.",
])
para("Cả hai hệ được gọi với cùng đầu vào: câu, loại sự kiện và từ kích hoạt. Bộ đánh giá không có thông tin chủ thể và "
     "đối tượng, nên hệ cơ sở chạy mà không biết vị trí đối tượng trong câu; đây là điều kiện bất lợi cho hệ cơ sở so "
     "với lúc nó chạy trong đường ống đầy đủ.")
heading("6.3. Thước đo", level=2)
para("Với mỗi trường, một dự đoán là *khớp chặt* nếu trùng nhãn tham chiếu sau khi bỏ phân biệt hoa thường, và *khớp mềm* "
     "nếu khớp chặt, hoặc một chuỗi chứa chuỗi kia, hoặc hệ số Jaccard trên tập từ đạt từ 0,5. Độ chính xác P là số khớp "
     "chia cho số dự đoán khác rỗng; độ phủ R là số khớp chia cho số nhãn; F1 là trung bình điều hòa. Chỉ số gộp tính "
     "theo kiểu vi mô trên cả bảy trường. Tốc độ đo bằng trung vị của 30 lần chạy sau khi khởi động, một luồng CPU, "
     "Python 3.11 trên máy tính xách tay.")

# ================================================================== 7
heading("7. Kết quả")
heading("7.1. So với nhãn tham chiếu", level=2)
table("Bảng 5. Kết quả theo từng trường trên 446 câu",
      ["Trường", "Số nhãn", "Dự đoán", "Chặt", "Mềm", "F1 mềm", "Dự đoán", "Chặt", "Mềm", "F1 mềm"],
      [["`legal_doc`", "80", "76", "75", "75", "96,2", "81", "80", "80", "99,4"],
       ["`deadline`", "7", "4", "4", "4", "72,7", "7", "7", "7", "100,0"],
       ["`urgency`", "42", "31", "31", "31", "84,9", "42", "42", "42", "100,0"],
       ["`appoint_type`", "136", "136", "136", "136", "100,0", "136", "115", "136", "100,0"],
       ["`role`", "91", "86", "83", "86", "97,2", "86", "74", "86", "97,2"],
       ["`penalty_form`", "46", "45", "45", "45", "98,9", "46", "45", "45", "97,8"],
       ["`action_content`", "95", "91", "59", "91", "97,8", "151", "36", "82", "66,7"],
       ["Gộp", "497", "469", "433", "468", "96,9", "549", "399", "478", "91,4"]],
      widths=[2.9, 1.4, 1.5, 1.2, 1.2, 1.5, 1.5, 1.2, 1.2, 1.5],
      align=["l"] + ["r"] * 9, size=9.5, bold_last=True,
      group_header=[("", 2), ("Hệ cơ sở", 4), ("ViGov-IE v2", 4)],
      note="Dự đoán: số câu hệ trả về giá trị khác rỗng. Chặt, Mềm: số dự đoán khớp chặt, khớp mềm với nhãn tham chiếu.")
table("Bảng 6. Chỉ số gộp vi mô trên bảy trường (%)",
      ["Hệ", "P", "R", "F1", "P", "R", "F1"],
      [["Hệ cơ sở", "92,3", "87,1", "89,6", "99,8", "94,2", "96,9"],
       ["ViGov-IE v2", "72,7", "80,3", "76,3", "87,1", "96,2", "91,4"]],
      widths=[3.6, 1.7, 1.7, 1.7, 1.7, 1.7, 1.7], align=["l"] + ["r"] * 6, size=10,
      group_header=[("", 1), ("Khớp chặt", 3), ("Khớp mềm", 3)])
figure("hinh6_f1_theo_truong.png",
       "Hình 6. F1 khớp mềm theo từng trường. Phiên bản 2 hơn hệ cơ sở ở ba trường có mẫu cố định, ngang ở các trường "
       "nhân sự, và thấp hơn rõ ở nội dung chỉ đạo, kéo chỉ số gộp xuống.", width=12.5)
para("Bảng 5, Bảng 6 và Hình 6 cho ba nhận xét.")
para("*Thứ nhất*, phiên bản 2 tìm được nhiều tham số hơn: độ phủ khớp mềm tăng từ 94,2% (468/497) lên 96,2% (478/497). "
     "Mức tăng đến từ `legal_doc` (+5), `deadline` (+3) và `urgency` (+11), nhờ bộ mẫu rộng hơn và việc trích hai trường "
     "sau cho mọi loại sự kiện.")
para("*Thứ hai*, phiên bản 2 trả về nhiều giá trị không có trong nhãn: số dự đoán tăng từ 469 lên 549, độ chính xác khớp "
     "mềm giảm từ 99,8% xuống 87,1%, và F1 gộp giảm từ 96,9% xuống 91,4%. Gần như toàn bộ phần dôi ra nằm ở "
     "`action_content` (151 dự đoán trên 95 nhãn): phiên bản 2 có thêm luật dự phòng cho sự kiện chủ trì, làm việc và "
     "phối hợp, nơi hệ cơ sở để trống. Nhãn tham chiếu không cho biết các giá trị thêm này đúng hay sai.")
para("*Thứ ba*, ở mức khớp chặt phiên bản 2 thua hệ cơ sở trên cả ba trường mở. Một phần là hệ quả tất yếu của việc nhãn "
     "là đầu ra của hệ cơ sở, nhưng soát từng trường hợp cho thấy hai lỗi thật của phiên bản 2, trình bày ở Mục 8.1: "
     "21 câu sai `appoint_type` và 7 câu cắt cụt `role`.")
para("Tóm lại, trên bộ nhãn này không thể kết luận phiên bản 2 tốt hơn hệ cơ sở về tổng thể. Điều có thể kết luận là nó "
     "phủ rộng hơn ở các trường có mẫu cố định và cho kết quả khác hẳn ở nội dung chỉ đạo; mục tiếp theo xét xem khác "
     "theo hướng nào.")

heading("7.2. Rà soát thủ công nội dung chỉ đạo", level=2)
para("Trong 95 câu có nhãn `action_content`, có 12 câu mà hệ cơ sở gần trùng nhãn (Jaccard trên 0,8) còn phiên bản 2 lệch "
     "xa (dưới 0,5). Đọc cả 12 câu cho thấy nhãn tham chiếu ở đây thường là đoạn cắt sai: lẫn trạng ngữ mở đầu, chủ thể "
     "và từ kích hoạt, hoặc chỉ là một mẩu vô nghĩa. Hai ví dụ:")
example("Câu:", "*Chỉ đạo một số nhiệm vụ cụ thể, Thủ tướng yêu cầu Bộ Xây dựng tiếp tục nghiên cứu, rà soát, hoàn thiện các văn bản quy phạm pháp luật để tháo gỡ khó khăn…*")
example("Nhãn tham chiếu:", "“một số nhiệm vụ cụ thể , Thủ tướng yêu cầu Bộ Xây dựng tiếp tục nghiên cứu , rà soát , hoàn thiện các văn bản quy phạm pháp luật”")
example("ViGov-IE v2:", "“nghiên cứu, rà soát, hoàn thiện các văn bản quy phạm pháp luật”").paragraph_format.space_after = Pt(8)
example("Nhãn tham chiếu (câu khác):", "“Cuối cùng”")
example("ViGov-IE v2:", "“Ban Tuyên giáo và Dân vận Trung ương phối hợp với Ban Chỉ đạo 35 của các cơ quan”").paragraph_format.space_after = Pt(8)
para("Để đo có hệ thống, chúng tôi lấy ngẫu nhiên 40 trong 92 câu chỉ đạo của bộ đánh giá (hạt giống cố định) và xếp đầu ra "
     "của mỗi hệ vào một trong bốn mức: *vị ngữ sạch* (chỉ gồm việc được chỉ đạo); *đúng nội dung nhưng còn dính cơ quan "
     "nhận lệnh* ở đầu; *lẫn chủ thể hoặc từ kích hoạt*, hoặc chỉ có tên cơ quan mà không có việc; và *không trích được*. "
     "Việc xếp mức do một người thực hiện, không qua nhãn tham chiếu.")
table("Bảng 7. Rà soát thủ công 40 câu chỉ đạo",
      ["Mức", "Hệ cơ sở", "ViGov-IE v2"],
      [["Vị ngữ sạch", "1 (2,5%)", "6 (15,0%)"],
       ["Đúng nội dung, còn dính cơ quan nhận lệnh", "13 (32,5%)", "23 (57,5%)"],
       ["Lẫn chủ thể hoặc từ kích hoạt", "8 (20,0%)", "1 (2,5%)"],
       ["Không trích được", "18 (45,0%)", "10 (25,0%)"],
       ["Dùng được (hai mức đầu)", "14 (35,0%)", "29 (72,5%)"]],
      widths=[7.6, 3.4, 3.4], align=["l", "r", "r"], size=10, bold_last=True)
figure("hinh7_ra_soat_thu_cong.png",
       "Hình 7. Phân bố bốn mức chất lượng trên 40 câu chỉ đạo. Phiên bản 2 gần như loại bỏ lỗi lẫn chủ thể và giảm gần "
       "một nửa số câu không trích được, nhưng phần lớn đầu ra vẫn còn dính cơ quan nhận lệnh.", width=12.5)
para("Kết quả ở Bảng 7 đảo ngược bức tranh của Mục 7.1 cho riêng trường này. Phiên bản 2 cho đầu ra dùng được ở 29 câu so "
     "với 14 câu; lỗi nặng nhất của hệ cơ sở, lẫn chủ thể và từ kích hoạt vào nội dung, giảm từ 8 câu xuống 1. Mức F1 "
     "66,7% của phiên bản 2 ở Bảng 5 vì thế chủ yếu phản ánh nhiễu của nhãn tham chiếu.")
para("Kết quả cũng cho thấy giới hạn của phiên bản 2. Chỉ 6 trên 40 câu cho vị ngữ sạch; ở 23 câu, tên cơ quan nhận lệnh "
     "vẫn nằm ở đầu nội dung, vì luật chỉ gỡ được nó khi theo sau là một từ đệm trong danh sách. Mười câu không trích "
     "được đều là câu có nội dung dài quá ngưỡng 220 ký tự. Mẫu 40 câu là nhỏ: khoảng tin cậy 95% (Wilson) của tỷ lệ "
     "dùng được là 57%–84% cho phiên bản 2 và 22%–51% cho hệ cơ sở; hai khoảng không giao nhau nhưng độ rộng của chúng "
     "cần được lưu ý.")

heading("7.3. Các nhóm câu khó", level=2)
para("Một trăm lẻ bốn câu của bộ đánh giá được chọn bằng mẫu để đại diện cho bốn hiện tượng: câu mở đầu bằng động từ, "
     "khuyết chủ ngữ (LH1); câu kỷ luật nêu từ hai hình thức trở lên (LH2); câu có từ hai chữ *nguyên* trở lên, tức liệt "
     "kê nhiều chức vụ cũ (LH4); và câu chứa cụm tham chiếu sang câu khác như *tại buổi lễ*, *nhân dịp này* (LH5). Một "
     "hiện tượng thứ năm, bị động qua cơ quan trung gian (LH3), không có câu nào trong 6.694 câu sự kiện khớp mẫu nhận "
     "diện.")
table("Bảng 8. Số câu có đầu ra theo từng nhóm câu khó",
      ["Nhóm", "Số câu", "Tiêu chí “có đầu ra”", "Hệ cơ sở", "ViGov-IE v2"],
      [["LH1 – khuyết chủ ngữ", "16", "Có ít nhất một trong `legal_doc`, `action_content`, `appoint_type`", "8", "13"],
       ["LH5 – tham chiếu liên câu", "27", "Như trên", "21", "22"],
       ["LH4 – nhiều chức vụ cũ", "51", "Có `role` và không chứa chữ “nguyên”", "2", "7"],
       ["LH2 – nhiều người, nhiều hình thức", "10", "Có `penalty_form`", "9", "9"],
       ["LH2 – ghép được từ hai cặp người–hình thức", "10", "`coordinated_items` có từ 2 phần tử", "–", "5"]],
      widths=[4.6, 1.4, 5.6, 1.7, 2.0], align=["l", "r", "l", "r", "r"], size=9.5,
      note="Tiêu chí chỉ kiểm tra đầu ra khác rỗng, không kiểm tra đầu ra đúng.")
para("Các con số ở Bảng 8 cần được đọc đúng với tiêu chí của chúng. Tiêu chí chỉ hỏi hệ có trả về giá trị hay không; nó "
     "không đo việc khôi phục chủ ngữ bị khuyết hay giải tham chiếu liên câu, và bộ trích xuất cũng không có cơ chế nào "
     "cho hai việc đó vì nó xử lý từng câu riêng rẽ. Mức tăng ở LH1 (8 lên 13) đến từ việc phiên bản 2 tìm từ kích hoạt "
     "tốt hơn trong câu bắt đầu bằng động từ. Ở LH4, chỉ 15 trên 51 câu là sự kiện nhân sự và chỉ 8 câu có nhãn `role`, "
     "nên mẫu số 51 làm tỷ lệ trông thấp hơn thực chất. Ở LH2, phiên bản 2 tách được từ hai cặp người–hình thức ở 5 trên "
     "10 câu; khả năng này hệ cơ sở không có, nhưng độ đúng của từng cặp chưa được chấm.")

heading("7.4. Khử trùng thực thể", level=2)
table("Bảng 9. Kết quả khử trùng trên 8.937 cạnh tin tức",
      ["Chỉ số", "Giá trị"],
      [["Cạnh tin tức ban đầu", "8.937"],
       ["Sau khi gộp theo định danh trùng khớp chính xác", "4.758"],
       ["Sau khi thêm luật phân rã", "4.583"],
       ["Thời gian chạy luật phân rã (trung vị 7 lần)", "khoảng 0,1 giây"],
       ["Cặp thực thể có độ tương đồng chuỗi từ 90% (trên 2.324 thực thể)", "1.447"],
       ["   trong đó bị luật phân rã chặn", "1.422 (98,3%)"],
       ["Cặp thực thể khác định danh được luật phân rã gộp khi gộp cạnh", "108"],
       ["   đúng: cùng một cơ quan", "2"],
       ["   chấp nhận được: cơ quan kế thừa hoặc cấp trung ương của cùng tổ chức", "8"],
       ["   sai: hai cơ quan khác nhau", "98 (90,7%)"]],
      widths=[11.2, 3.4], align=["l", "r"], size=10)
figure("hinh8_ket_qua_khu_trung.png",
       "Hình 8. (a) Số cạnh sau từng bước gộp. (b) Phân loại thủ công 108 cặp thực thể mà luật phân rã gộp thêm so với "
       "gộp trùng khớp chính xác.", width=12.5)
para("Luật phân rã làm tốt việc nó nhắm tới: trong 1.447 cặp dễ bị so khớp mờ gộp nhầm, luật chặn 1.422 cặp. Hai mươi lăm "
     "cặp còn lọt chủ yếu là Tòa án nhân dân và Ủy ban nhân dân của cùng một tỉnh, hoặc Sở Ngoại vụ và Sở Nội vụ.")
para("Nhưng phần gộp mà luật thực hiện thì phần lớn sai. So với gộp trùng khớp chính xác, luật giảm thêm 175 cạnh, tương "
     "ứng 108 cặp thực thể khác định danh được coi là một. Soát cả 108 cặp: 2 cặp đúng là một cơ quan viết hai cách (ví "
     "dụ Sở Giáo dục và Đào tạo Hà Nội có và không có chữ *thành phố*); 8 cặp là cơ quan kế thừa sau sáp nhập hoặc cấp "
     "trung ương của cùng tổ chức; 98 cặp là hai cơ quan khác hẳn nhau ở cùng địa phương, như Tỉnh ủy với Ủy ban nhân "
     "dân tỉnh, Sở Nội vụ với Sở Y tế, Công an tỉnh với Sở Công Thương. Nguyên nhân là phép so tiền tố mô tả ở Mục 5.2. "
     "Luật cũng không gộp được biến thể viết tắt như *Sở KH và ĐT* với *Sở Kế hoạch và Đầu tư*.")
para("Kết luận thực tiễn: ở trạng thái hiện tại, gộp theo định danh trùng khớp chính xác (4.758 cạnh) an toàn hơn luật "
     "phân rã. Ý tưởng so tên lõi trước là đúng và đáng giữ; phần cần thay là phép so tiền tố (Mục 9).")

heading("7.5. Tốc độ", level=2)
table("Bảng 10. Tốc độ xử lý trên một luồng CPU",
      ["Hệ", "446 câu đánh giá (câu/giây)", "6.694 câu sự kiện (câu/giây)"],
      [["Hệ cơ sở (có underthesea)", "262", "164"],
       ["ViGov-IE v2", "8.078", "12.887"],
       ["Tỷ lệ", "31 lần", "79 lần"]],
      widths=[5.4, 4.6, 4.6], align=["l", "r", "r"], size=10, bold_last=True)
para("Phiên bản 2 nhanh hơn hệ cơ sở từ 31 đến 79 lần tùy tập câu (Bảng 10). Toàn bộ khoảng cách đến từ việc hệ cơ sở gọi "
     "bộ phân cụm cú pháp cho mỗi câu chỉ đạo, còn phiên bản 2 chỉ dùng biểu thức chính quy. Con số tuyệt đối phụ thuộc "
     "máy và dao động giữa các lần chạy (6.500–8.600 câu/giây trên bộ đánh giá); ở tốc độ này, 6.694 câu sự kiện được xử "
     "lý trong khoảng nửa giây.")

# ================================================================== 8
heading("8. Thảo luận và hạn chế")
heading("8.1. Lỗi đã xác định trong phiên bản 2", level=2)
bullets([
    "**Hình thức “điều động, bổ nhiệm”.** Mẫu nhận diện *Điều động và bổ nhiệm* không khớp khi sau dấu phẩy có khoảng trắng, nên cả 21 câu dạng “điều động, bổ nhiệm ông …” bị gán thành *Điều động*. Hệ cơ sở xử lý đúng các câu này. Lỗi bị che ở mức khớp mềm vì *Điều động* là chuỗi con của nhãn.",
    "**Chữ “nguyên” trong địa danh.** Thao tác bỏ chức vụ cũ tách chuỗi tại chữ *nguyên* không phân biệt hoa thường, nên *Bí thư Tỉnh ủy Thái Nguyên* thành *Bí thư Tỉnh ủy Thái* và *Bộ trưởng Bộ Tài nguyên và Môi trường* thành *Bộ trưởng Bộ Tài*. Bảy câu trong bộ đánh giá mắc lỗi này.",
    "**Mệnh đề mục đích.** Bộ trích xuất trong `extraction/` ngắt nội dung chỉ đạo tại *nhằm* và *để*, nên bỏ mất phần mục đích. Bản thử nghiệm trong `scratch/` không ngắt ở hai từ này nhưng lại có độ phủ thấp hơn trên nhãn tham chiếu (77,9% so với 86,3%); hai bản chưa được thống nhất.",
    "**Dư ký tự sau khi bỏ thời hạn.** Khi cụm thời hạn bị cắt khỏi nội dung chỉ đạo, phần còn lại của ngày tháng có thể sót lại (ví dụ “…, hoàn thành 26”).",
    "**Luật khử trùng.** Phép so tiền tố bằng `token_set_ratio` gộp nhầm các cơ quan cùng địa phương (Mục 7.4).",
])
heading("8.2. Thành phần chưa được cài đặt", level=2)
para("Một số ý tưởng đã được nêu trong quá trình thiết kế nhưng không có trong mã nguồn hiện tại, và vì thế không có trong "
     "bất kỳ kết quả nào của bài báo này:")
bullets([
    "Che thực thể theo vị trí trước khi cắt nội dung chỉ đạo. Đây là cách trực tiếp để xử lý 23 câu còn dính cơ quan nhận lệnh ở Bảng 7.",
    "Bộ đệm ngữ cảnh liên câu để kế thừa chủ thể cho câu khuyết chủ ngữ.",
    "Đối sánh chức vụ với từ điển 1.563 nút Chức vụ. Bộ trích xuất có nạp từ điển này nhưng chưa dùng đến.",
    "Hàm tách cơ quan đề nghị và cơ quan quyết định trong câu bị động đã có trong mã nhưng không kích hoạt trên câu nào của 6.694 câu sự kiện.",
])
heading("8.3. Hạn chế của phép đánh giá", level=2)
bullets([
    "Nhãn tham chiếu là nhãn tự động (Mục 6.1). Điểm số trên 446 câu không thay thế được đánh giá trên nhãn do người gán.",
    "Rà soát thủ công chỉ gồm 40 câu, một người chấm, một trường. Chưa có độ đồng thuận giữa nhiều người chấm.",
    "Phân loại 108 cặp thực thể ở Mục 7.4 cũng do một người thực hiện; ranh giới giữa *chấp nhận được* và *sai* ở các cặp cơ quan kế thừa có thể tranh luận, nhưng không ảnh hưởng đến kết luận.",
    "Hai tham số `tenure` và `violation_reason` chưa được đánh giá.",
    "Bộ trích xuất nhận loại sự kiện và từ kích hoạt từ thượng nguồn; lỗi ở bước đó không được tính ở đây.",
    "Hai con số về quy mô ngữ liệu thô (số bài báo, số trang Wikipedia) không được đếm lại.",
])

# ================================================================== 9
heading("9. Kết luận và hướng phát triển")
para("Bài báo mô tả ViGov-IE, một bộ trích xuất bằng luật đưa các chi tiết của sự kiện quản lý nhà nước vào đồ thị tri thức "
     "dưới dạng tham số trên nút sự kiện, và kiểm định lại các kết quả của nó. Ba kết luận đứng vững sau kiểm định. Một, "
     "phiên bản 2 mở rộng độ phủ ở các tham số có mẫu cố định và nhanh hơn hệ cơ sở hàng chục lần vì không cần phân cụm "
     "cú pháp. Hai, ở nội dung chỉ đạo, rà soát thủ công cho thấy phiên bản 2 tốt hơn rõ rệt (29 so với 14 câu dùng được "
     "trên 40), dù điểm trên nhãn tự động nói ngược lại; nhãn tự động chép từ hệ cơ sở không đủ để so hai hệ ở trường "
     "này. Ba, luật khử trùng theo phân rã chặn được bẫy trùng tiền tố nhưng gộp nhầm các cơ quan cùng địa phương, và "
     "chưa nên dùng thay cho gộp trùng khớp chính xác.")
para("Các việc tiếp theo, theo thứ tự ưu tiên:", after=3)
bullets([
    "Sửa bốn lỗi cục bộ ở Mục 8.1; mỗi lỗi chỉ cần thay một mẫu hoặc một điều kiện và đã có sẵn câu kiểm thử trong bộ đánh giá.",
    "Thay phép so tiền tố trong luật khử trùng bằng so trùng khớp sau khi chuẩn hóa qua bảng viết tắt (*UBND*, *KH và ĐT*, *TP*), và chỉ gộp khi tiền tố chuẩn hóa giống hệt nhau.",
    "Dựng một bộ nhãn do người gán, bắt đầu từ 92 câu chỉ đạo và các câu nhân sự, có ít nhất hai người chấm, để thay nhãn tự động.",
    "Cài đặt che thực thể theo vị trí cho nội dung chỉ đạo và đo lại bằng đúng quy trình rà soát ở Mục 7.2.",
    "Thử chuyển riêng các câu mà luật không trích được sang một mô hình ngôn ngữ nhỏ, giữ luật làm đường xử lý chính.",
], numbered=True)

# ================================================================== Tài liệu tham khảo
heading("Tài liệu tham khảo")
refs = [
    "[1] T.-N. Nguyen, B. T. Tran, T.-N. Luu, T. H. Nguyen, K.-H. Nguyen. *BKEE: Pioneering Event Extraction in the Vietnamese Language*. Proceedings of LREC-COLING 2024, tr. 2421–2427, 2024.",
    "[2] D. Truong, D.-T. Vo, U. T. Nguyen. *Vietnamese Open Information Extraction*. Proceedings of the 8th International Symposium on Information and Communication Technology (SoICT), 2017. arXiv:1801.07804.",
    "[3] V. T. Mai, H.-Q. Le, D.-C. Can, T. M. H. Nguyen, T. N. L. Nguyen, T. T. Doan. *Overview of VLSP RelEx shared task: A Data Challenge for Semantic Relation Extraction from Vietnamese News*. Proceedings of the 7th International Workshop on Vietnamese Language and Speech Processing (VLSP), tr. 92–98, 2020.",
    "[4] D. Q. Nguyen, A. T. Nguyen. *PhoBERT: Pre-trained language models for Vietnamese*. Findings of EMNLP 2020, tr. 1037–1042, 2020.",
    "[5] P. Christen. *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection*. Springer, 2012.",
    "[6] M. Bachmann. *RapidFuzz: Rapid fuzzy string matching in Python* (phần mềm). https://github.com/rapidfuzz/RapidFuzz.",
    "[7] G. Doddington, A. Mitchell, M. Przybocki, L. Ramshaw, S. Strassel, R. Weischedel. *The Automatic Content Extraction (ACE) Program – Tasks, Data, and Evaluation*. Proceedings of LREC 2004.",
    "[8] A. Hogan và cộng sự. *Knowledge Graphs*. ACM Computing Surveys, 54(4), 2021.",
    "[9] Underthesea – Vietnamese NLP Toolkit (phần mềm). https://github.com/undertheseanlp/underthesea.",
]
for ref in refs:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.8)
    pf.first_line_indent = Cm(-0.8)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.1
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_runs(p, ref, size=11)

# ================================================================== Phụ lục
heading("Phụ lục A. Tái lập kết quả")
para("Mọi số liệu ở Mục 7 được sinh bởi các tệp lệnh sau, chạy từ thư mục gốc của kho mã. Cần các thư viện `rapidfuzz`, "
     "`underthesea`, `matplotlib`, `python-docx`.", after=4)
table("Bảng A1. Tệp lệnh và kết quả tương ứng",
      ["Tệp lệnh", "Sinh ra"],
      [["`scratch/verify_claims.py`", "Bảng 2–6, 8, 10; số liệu lưu ở `report/verified_metrics.json`"],
       ["`scratch/verify_dedup.py`", "Bảng 9: số cạnh, số cặp tương đồng, danh sách cặp bị gộp (`data/eval/dedup_merged_pairs_raw.csv`)"],
       ["`data/eval/manual_audit_action_content.csv`", "Bảng 7: 40 câu, đầu ra của hai hệ và mức được xếp"],
       ["`data/eval/manual_audit_dedup_pairs.csv`", "Bảng 9: 108 cặp thực thể và phân loại"],
       ["`report/generate_paper_figures.py`", "Hình 1–8"],
       ["`report/build_paper_docx.py`", "Tệp báo cáo này"]],
      widths=[7.4, 7.6], align=["l", "l"], size=9.5)

doc.core_properties.title = "ViGov-IE: Trích xuất tham số sự kiện N-ngôi bằng luật cú pháp"
doc.core_properties.author = "Nhóm thực hiện Đề tài 19"
try:
    doc.save(OUT)
    print("Đã lưu:", OUT.relative_to(ROOT))
except PermissionError:
    alt_out = OUT.parent / (OUT.stem + "_CapNhat.docx")
    doc.save(alt_out)
    print(f"⚠️ {OUT.name} đang mở trong Word. Đã lưu bản cập nhật tại: {alt_out.name}")
