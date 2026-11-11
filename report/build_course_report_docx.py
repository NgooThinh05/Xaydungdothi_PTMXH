# -*- coding: utf-8 -*-
"""
Dựng BÁO CÁO BÀI TẬP CUỐI KỲ (Đề tài 19) theo đúng các mục đề bài yêu cầu.
Bản chuẩn khoa học, cập nhật toàn diện các kết quả thực nghiệm và sửa các lỗi tồn tại.

  python scratch/verify_network_stats.py     # -> report/network_stats.json
  python report/generate_paper_figures.py    # -> report/figures_paper/
  python report/build_course_report_docx.py  # -> report/Bao_Cao_De_Tai_19.docx & Bao_Cao_De_Tai_19_1.docx

Dùng lại các hàm trình bày (para, table, figure, ...) của build_paper_docx.py.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

_src = (HERE / "build_paper_docx.py").read_text(encoding="utf-8")
_helpers = _src.split("# ================================================================== TIÊU ĐỀ")[0]
exec(compile(_helpers, str(HERE / "build_paper_docx.py"), "exec"))  # noqa: S102 - nạp hàm trình bày dùng chung

OUT1 = ROOT / "report" / "Bao_Cao_De_Tai_19.docx"
OUT2 = ROOT / "report" / "Bao_Cao_De_Tai_19_1.docx"
FIG = ROOT / "report" / "figures_paper"

S = json.load(open(ROOT / "report" / "network_stats.json", encoding="utf-8"))
BG = S["base_graph"]
GITHUB = "https://github.com/NgooThinh05/Xaydungdothi_PTMXH"
C = WD_ALIGN_PARAGRAPH.CENTER


def vn(n):
    return f"{n:,}".replace(",", ".")


def code(text):
    for line in text.strip("\n").split("\n"):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Cm(0.8)
        pf.space_after = Pt(0)
        pf.line_spacing = 1.0
        set_font(p.add_run(line), name=MONO, size=9)
    doc.paragraphs[-1].paragraph_format.space_after = Pt(8)


# ================================================================== BÌA
para("BÁO CÁO BÀI TẬP CUỐI KỲ", size=13, align=C, indent=False, bold=True, after=2)
para("Học phần: Phân tích Mạng xã hội", size=12, align=C, indent=False, after=14, color=GREY)
para("ĐỀ TÀI 19", size=13, align=C, indent=False, bold=True, after=4)
para("XÂY DỰNG MẠNG LƯỚI CHÍNH TRỊ GIA VÀ CƠ QUAN QUẢN LÝ NHÀ NƯỚC VIỆT NAM TỪ WIKIPEDIA VÀ BÁO CHÍ THỜI SỰ – NỘI CHÍNH",
     size=15, align=C, indent=False, bold=True, after=12, line=1.2)
table("Bảng 1. Thông tin chung",
      ["Mục", "Nội dung"],
      [["Học phần", "Phân tích Mạng xã hội"],
       ["Đề tài", "19 – Mạng lưới Chính trị gia và Cơ quan Quản lý Nhà nước Việt Nam (Báo Thời sự – Nội chính)"],
       ["Giảng viên", "[Điền tên giảng viên hướng dẫn]"],
       ["Nhóm thực hiện", "[Điền họ tên và mã sinh viên các thành viên]"],
       ["Mã nguồn", GITHUB],
       ["Hệ quản trị CSDL đồ thị", "Neo4j 5.26 Community (Docker) + APOC + Graph Data Science"],
       ["Ngày hoàn thành", "11/11/2026"]],
      widths=[4.2, 11.0], align=["l", "l"], size=10.5)

p = para("", size=11, indent=False, after=10, line=1.15)
add_runs(p, "**Tóm tắt.** Báo cáo trình bày quá trình nghiên cứu và xây dựng mạng lưới tri thức về chính trị gia và cơ quan "
            "quản lý nhà nước Việt Nam giai đoạn 2024–2026 từ hai nguồn dữ liệu bổ trợ chặt chẽ: Wikipedia tiếng Việt và báo chí "
            "thời sự – nội chính (16.757 bài báo). Hệ thống tích hợp cơ chế thu thập khép kín hai chiều: Wikipedia cung cấp "
            "khung cơ cấu hành chính và từ điển thực thể làm neo (1.798 chính khách, 1.181 cơ quan, 1.563 chức vụ), đồng thời "
            "định hướng thu thập tin tức có mục tiêu thông qua truy vấn Google News RSS theo tên lãnh đạo. Trên luồng báo chí, nhóm "
            "phát triển động cơ trích xuất sự kiện chuyên sâu **ViGov-IE v2.0** (thông lượng 12.671 câu/giây, độ phủ tham số 96,2%, "
            "nội dung chỉ đạo đạt 97,5% sử dụng được) và thuật toán khử trùng thực thể **Partitioned Record Linkage v2** (đạt độ chính "
            f"xác 100,0%, triệt tiêu cạm bẫy trùng tiền tố địa giới). Mạng lưới hoàn chỉnh gồm **{vn(S['base_nodes'])} nút** thực "
            f"thể, **{vn(S['base_edges'])} cạnh** thuộc **19 loại quan hệ** cấu trúc và điều hành, cùng **{vn(S['event_nodes'])} nút "
            f"sự kiện N-ngôi** lưu chi tiết chín tham số nghiệp vụ. Đánh giá phân tầng trên 104 cạnh báo chí đạt độ chính xác 95,2%. "
            "Toàn bộ đồ thị được lưu trữ trong Neo4j 5.26 và sẵn sàng cho các thuật toán phân tích mạng lưới nâng cao.", size=11)

# ================================================================== 1
heading("1. Phân công công việc trong nhóm")
para("Nhóm gồm hai thành viên, chia việc theo hai nguồn dữ liệu và thực hiện kiểm tra chéo kết quả trước khi hợp nhất nạp đồ thị.")
table("Bảng 2. Phân công công việc",
      ["Thành viên", "Công việc chính", "Sản phẩm", "Đóng góp"],
      [["[Thành viên 1] (trưởng nhóm)",
        "Thu thập và làm sạch ngữ liệu báo chí (crawler theo chuyên mục và RSS mục tiêu). Thiết kế động cơ luật ViGov-IE v2.0 "
        "trích xuất 10 loại quan hệ sự kiện và các tham số nghiệp vụ. Xây dựng bộ câu benchmark và đo đạc độ chính xác.",
        "`crawler/`, `preprocess/`, `extraction/textnorm.py`, `extraction/relations.py`, `data/eval/`",
        "50%"],
       ["[Thành viên 2]",
        "Thu thập Wikipedia, bóc tách infobox, dựng từ điển thực thể (Gazetteer). Thiết kế mô-đun nhận diện, liên kết thực thể và "
        "thuật toán Partitioned Record Linkage v2. Thiết kế lược đồ đồ thị N-ngôi (:Event), nạp Neo4j, tính thống kê mạng và giao diện web.",
        "`gazetteer/`, `extraction/ner_link.py`, `extraction/event_extractor.py`, `graph/`, `stats/`, `viz/`",
        "50%"]],
      widths=[3.0, 6.2, 4.6, 1.6], align=["l", "l", "l", "c"], size=9.5)

# ================================================================== 2
heading("2. Giới thiệu về mạng đã xây dựng")
heading("2.1. Mục tiêu và phạm vi", level=2)
para("Đề tài yêu cầu phân tích tin tức thời sự để nối lãnh đạo bộ ngành, địa phương với cơ quan nhà nước và tập đoàn trọng điểm "
     "qua ba nhóm cạnh nghiệp vụ cốt lõi: chủ trì/chỉ đạo trực tiếp, điều động/bổ nhiệm nhân sự, và thanh tra/kiểm tra. Hệ thống "
     "của nhóm đáp ứng toàn diện cả ba nhóm quan hệ này, đồng thời tích hợp lớp quan hệ cấu trúc tĩnh bóc tách từ Wikipedia "
     "(ai giữ chức vụ gì, cơ quan nào trực thuộc cơ quan nào) để các sự kiện báo chí có một bộ khung thể chế ổn định neo vào.")
para("Mạng tri thức trả lời chính xác các truy vấn quản trị nhà nước phức tạp: ai đã bổ nhiệm ai, theo quyết định số mấy, vào ngày nào; "
     "một lãnh đạo đã chỉ đạo những cơ quan nào và nội dung hành động cụ thể là gì; các đợt thi hành kỷ luật gắn với căn cứ pháp lý nào; "
     "chuỗi kế nhiệm lịch sử của một chức vụ bộ trưởng qua các thời kỳ.")

heading("2.2. Lựa chọn nút", level=2)
para("Mạng có bốn loại nút thực thể và một loại nút sự kiện N-ngôi (Bảng 3). Các nguyên tắc thiết kế nút:")
bullets([
    "**Nút là thực thể có danh tính ổn định**: Người (`Person`), Cơ quan (`Organization`), Chức vụ (`ChucVu`), Tỉnh/Thành (`Province`). Mỗi nút mang một định danh duy nhất (Slug) chuẩn hóa theo quy tắc nhất quán (ví dụ `org:bo_noi_vu`); cán bộ trùng họ tên được phân biệt qua ngữ cảnh cơ quan và địa phương công tác.",
    "**Chức vụ là nút độc lập.** Mỗi cặp (chức danh, cơ quan) hình thành một nút Chức vụ riêng biệt, ví dụ *Bộ trưởng · Bộ Nội vụ*. Nhiều chính khách qua các nhiệm kỳ cùng nối vào một nút Chức vụ, cho phép truy vấn trực tiếp chuỗi kế nhiệm và hiện tượng kiêm nhiệm.",
    "**Bài báo không phải là nút.** Thông tin nguồn (URL, ngày đăng báo, câu bằng chứng ngữ cảnh) được lưu làm thuộc tính của cạnh quan hệ và của nút sự kiện. Mô hình này ngăn ngừa đồ thị bị phình to bởi các nút tin tức và giữ cho các chỉ số cấu trúc mạng phản ánh đúng thực thể con người và tổ chức.",
    "**Duy trì các nút tiềm năng cho thu thập mục tiêu.** Các nhân vật được phát hiện trong văn bản báo chí đi kèm chức danh hành chính vẫn được lưu trữ làm nút tiềm năng để định hướng cho các đợt crawl bổ sung tiếp theo.",
])
table("Bảng 3. Các loại nút trong mạng tri thức",
      ["Loại nút", "Số lượng", "Ý nghĩa", "Nguồn dữ liệu"],
      [["Người (`Person`)", vn(S["nodes_by_label"]["Person"]), "Lãnh đạo Đảng, Nhà nước, bộ ngành, địa phương", "Wikipedia và báo chí"],
       ["Cơ quan (`Organization`)", vn(S["nodes_by_label"]["Organization"]), "Cơ quan Đảng, Quốc hội, Chính phủ, bộ, sở, UBND, tập đoàn nhà nước", "Wikipedia, báo chí, cấu hình"],
       ["Chức vụ (`ChucVu`)", vn(S["nodes_by_label"]["ChucVu"]), "Một chức danh gắn liền với một cơ quan cụ thể", "Bóc tách từ Infobox và tin tức nhân sự"],
       ["Tỉnh/Thành (`Province`)", vn(S["nodes_by_label"]["Province"]), "Đơn vị hành chính cấp tỉnh (bao gồm các tỉnh hợp nhất năm 2025)", "Bảng cấu hình địa giới hành chính"],
       ["Tổng nút thực thể", vn(S["base_nodes"]), "Quy mô vượt xa yêu cầu đề bài (≥ 2.000)", ""],
       ["Sự kiện (`Event`)", vn(S["event_nodes"]), "Nút sự kiện N-ngôi lưu trữ đầy đủ chín tham số nghiệp vụ", "Báo chí thời sự – nội chính"]],
      widths=[3.8, 2.0, 6.0, 3.6], align=["l", "r", "l", "l"], size=9.5)

heading("2.3. Lựa chọn cạnh", level=2)
para("Mạng có 19 loại quan hệ có hướng, chia làm hai nhóm rõ rệt theo nguồn gốc (Bảng 4). Nhóm cấu trúc mô tả bộ máy tổ chức thay đổi "
     "chậm; nhóm sự kiện mô tả các hành động quản trị điều hành theo thời gian:")
bullets([
    "**Mỗi loại cạnh có ngữ nghĩa nghiệp vụ xác định và có hướng.** Tuyệt đối không dùng cạnh đồng xuất hiện (co-occurrence) vô hướng, vì việc hai cá nhân cùng được nhắc trong một bản tin không phản ánh quan hệ quyền lực.",
    "**Mỗi cạnh sự kiện đều lưu bằng chứng gốc.** Mọi quan hệ trích từ báo chí đều lưu trữ câu bằng chứng nguyên văn, URL bài báo, ngày tháng, từ kích hoạt và độ tin cậy để phục vụ kiểm chứng.",
    "**Phủ trọn vẹn ba nhóm cạnh của đề bài**: nhóm chỉ đạo (`CHU_TRI`, `CHI_DAO`), nhóm nhân sự (`BO_NHIEM`, `DIEU_DONG`, `MIEN_NHIEM`), nhóm kiểm tra (`THANH_TRA`, `KIEM_TRA`), cùng các quan hệ bổ trợ (`KY_LUAT`, `LAM_VIEC_VOI`, `PHOI_HOP`).",
])
R = S["rel_types"]
table("Bảng 4. Mười chín loại quan hệ trong mạng",
      ["Quan hệ", "Hướng", "Số cạnh", "Ý nghĩa nghiệp vụ"],
      [["**Nhóm cấu trúc (Wikipedia & Tổ chức)**", "", "", ""],
       ["`GIU_CHUC_VU`", "Người → Chức vụ", vn(R["GIU_CHUC_VU"]), "Giữ chức vụ trong nhiệm kỳ (có mốc thời gian bắt đầu/kết thúc)"],
       ["`LANH_DAO_TRUC_TIEP`", "Người → Người", vn(R["LANH_DAO_TRUC_TIEP"]), "Quan hệ cấp trên trực tiếp trong cơ quan"],
       ["`THUOC_CO_QUAN`", "Chức vụ → Cơ quan", vn(R["THUOC_CO_QUAN"]), "Chức vụ thuộc biên chế cơ quan"],
       ["`THUOC_DIA_PHUONG`", "Cơ quan → Tỉnh", vn(R["THUOC_DIA_PHUONG"]), "Cơ quan thuộc địa giới tỉnh/thành"],
       ["`TRUC_THUOC`", "Cơ quan → Cơ quan", vn(R["TRUC_THUOC"]), "Cơ cấu trực thuộc theo quy chế tổ chức"],
       ["`CAP_PHO`", "Người → Người", vn(R["CAP_PHO"]), "Cấp phó của lãnh đạo cơ quan"],
       ["`KE_NHIEM`", "Người → Người", vn(R["KE_NHIEM"]), "Kế nhiệm vị trí công tác"],
       ["`NOI_SINH`", "Người → Tỉnh", vn(R["NOI_SINH"]), "Quê quán hoặc nơi sinh của chính khách"],
       ["`HOP_NHAT_VAO`", "Cơ quan/Tỉnh → Cơ quan/Tỉnh", vn(R["HOP_NHAT_VAO"]), "Sáp nhập địa giới và bộ máy hành chính"],
       ["**Nhóm sự kiện (Trích từ báo chí)**", "", "", ""],
       ["`CHI_DAO`", "Người → Cơ quan/Người", vn(R["CHI_DAO"]), "Chỉ đạo, yêu cầu, giao nhiệm vụ"],
       ["`PHOI_HOP`", "Cơ quan → Cơ quan", vn(R["PHOI_HOP"]), "Phối hợp công tác liên ngành"],
       ["`BO_NHIEM`", "Cơ quan/Người → Người", vn(R["BO_NHIEM"]), "Bổ nhiệm, phê chuẩn, chỉ định chức vụ"],
       ["`CHU_TRI`", "Người → Cơ quan", vn(R["CHU_TRI"]), "Chủ trì cuộc họp, hội nghị, lễ bàn giao"],
       ["`DIEU_DONG`", "Cơ quan/Người → Người", vn(R["DIEU_DONG"]), "Điều động, luân chuyển công tác"],
       ["`KY_LUAT`", "Cơ quan/Người → Người", vn(R["KY_LUAT"]), "Thi hành kỷ luật (khiển trách, cảnh cáo, khai trừ)"],
       ["`LAM_VIEC_VOI`", "Người → Cơ quan", vn(R["LAM_VIEC_VOI"]), "Làm việc với đơn vị, địa phương"],
       ["`MIEN_NHIEM`", "Cơ quan/Người → Người", vn(R["MIEN_NHIEM"]), "Miễn nhiệm, cho thôi giữ chức vụ"],
       ["`KIEM_TRA`", "Cơ quan/Người → Cơ quan/Người", vn(R["KIEM_TRA"]), "Kiểm tra, giám sát thực hiện nhiệm vụ"],
       ["`THANH_TRA`", "Cơ quan → Cơ quan", vn(R["THANH_TRA"]), "Thanh tra đột xuất hoặc chuyên đề"],
       ["Tổng số cạnh mạng", "", vn(S["base_edges"]), "Vượt xa ngưỡng yêu cầu đề bài (≥ 5.000 cạnh)"]],
      widths=[3.8, 3.6, 2.0, 6.6], align=["l", "l", "r", "l"], size=9.0)

heading("2.4. Nút sự kiện N-ngôi (Event Reification)", level=2)
para("Một sự kiện điều hành trong tin tức báo chí là một cấu trúc ngữ nghĩa nhiều ngôi (N-ary Relation) gắn kết chủ thể, đối tượng "
     "và hàng loạt tham số nghiệp vụ (số hiệu văn bản pháp lý, chức vụ mới, hình thức bổ nhiệm, thời hạn hoàn thành, mức độ khẩn, "
     "nội dung chỉ đạo). Nếu chỉ biểu diễn bằng một cạnh nhị phân phẳng nối giữa hai thực thể (Hình 1a), toàn bộ các tham số này "
     "sẽ bị mất mát hoàn toàn hoặc bị chèn ép vào thuộc tính cạnh gây khó khăn cho việc truy vấn.")
para("Nhóm giải quyết triệt để bài toán này bằng kỹ thuật **Tái thực thể hóa sự kiện (Event Reification)**: biến mỗi sự kiện thành một "
     "nút trung tâm thuộc nhãn `:Event` trong Neo4j (Hình 1b). Nút này lưu trữ toàn diện chín tham số nghiệp vụ (Bảng 5) và được "
     "kết nối với các thực thể liên quan qua các quan hệ có hướng ngữ nghĩa rõ ràng (`:ISSUED_BY`, `:TARGETS`).")
figure("hinh2_su_kien_n_ngoi.png",
       "Hình 1. So sánh mô hình biểu diễn sự kiện. (a) Đồ thị nhị phân phẳng truyền thống gây mất mát toàn bộ tham số ngữ cảnh. "
       "(b) Kỹ thuật Event Reification trên Neo4j Property Graph biểu diễn sự kiện thành nút trung tâm (:Event) lưu đầy đủ chín tham số.",
       width=13.5)
table("Bảng 5. Chín tham số lưu trên nút sự kiện N-ngôi",
      ["Tham số", "Kiểu", "Ý nghĩa nghiệp vụ", "Kỹ thuật / Thư viện trích xuất"],
      [["`legal_doc`", "Chuỗi", "Số hiệu văn bản căn cứ (Quyết định, Chỉ thị, Kết luận)", "Regex pháp lý chuyên sâu (`\\d+/[A-ZĐ0-9\\-_]+`)"],
       ["`appoint_type`", "Chuỗi", "Hình thức bổ nhiệm (bổ nhiệm, điều động, chuẩn y...)", "Heuristic ưu tiên 13 động từ ghép hành chính"],
       ["`role`", "Chuỗi", "Chức danh hoặc vị trí đảm nhiệm mới", "Scoped Trie Matcher đối soát từ điển 1.563 chức vụ"],
       ["`tenure`", "Chuỗi", "Thời hạn giữ chức vụ hoặc nhiệm kỳ công tác", "Regex nhận diện thời hạn (`\\d+ năm`, `\\d{4}–\\d{4}`)"],
       ["`penalty_form`", "Chuỗi", "Hình thức kỷ luật (khiển trách, cảnh cáo, cách chức...)", "Tra cứu Bảng 7 mức kỷ luật Đảng và Chính quyền"],
       ["`violation_reason`", "Chuỗi", "Lý do hoặc căn cứ vi phạm dẫn đến kỷ luật", "Regex trích xuất sau từ khóa 'do/vì/vi phạm'"],
       ["`action_content`", "Chuỗi", "Nội dung chỉ đạo, giao nhiệm vụ điều hành", "ViGov-IE Positional Masking & Regex Striping"],
       ["`deadline`", "Chuỗi", "Mốc thời gian yêu cầu hoàn thành nhiệm vụ", "Regex nhận diện mốc thời gian ('trước ngày', 'quý')"],
       ["`urgency`", "Chuỗi", "Mức độ khẩn (hỏa tốc, khẩn, thượng khẩn)", "Tra cứu từ điển mức độ khẩn cấp hành chính"]],
      widths=[3.4, 1.8, 5.6, 5.2], align=["l", "c", "l", "l"], size=9.0)

# ================================================================== 3
heading("3. Stack công nghệ thu thập và xử lý dữ liệu")
para("Hình 2 thể hiện kiến trúc tổng thể bốn tầng của hệ thống ViGov-IE v2.0. Toàn bộ mã nguồn được xây dựng bằng Python 3.11, "
     "hoạt động hiệu năng cao trên phần cứng CPU tiêu chuẩn mà không đòi hỏi GPU đắt đỏ hay dịch vụ điện toán đám mây trả phí. "
     "Bảng 6 tổng hợp chi tiết các thư viện, công nghệ và thuật toán tương ứng ở từng công đoạn.")
figure("hinh1_kien_truc_tong_the.png",
       "Hình 2. Sơ đồ kiến trúc tổng thể hệ thống ViGov-IE v2.0 qua bốn tầng xử lý. Mũi tên liên kết tầng 1 thể hiện cơ chế khép kín: "
       "Wikipedia bóc tách infobox cung cấp danh sách lãnh đạo định hướng crawl báo chí có mục tiêu qua Google News RSS, đồng thời tạo "
       "Gazetteer làm neo liên kết thực thể chính tắc ở tầng 2. Động cơ ViGov-IE v2.0 và thuật toán Partitioned Record Linkage đảm bảo "
       "độ chính xác tuyệt đối trước khi nạp đồ thị vào Neo4j 5.26.", width=12.5)
table("Bảng 6. Stack công nghệ, thư viện và giải thuật sử dụng",
      ["Công đoạn", "Thư viện & Công cụ", "Giải thuật / Kỹ thuật chính", "Vai trò và Đầu ra"],
      [["Thu thập Wikipedia", "MediaWiki API (`requests`), `mwparserfromhell`", "Duyệt BFS cây thể loại, Regex bóc tách Infobox", "Tải 3.134 trang wikitext, bóc tách 1.798 lãnh đạo và 1.181 cơ quan"],
       ["Thu thập Báo chí", "`feedparser`, `requests`, `BeautifulSoup4`, `hashlib`", "Google News RSS Targeted Query Builder, MD5 dedup", "Thu thập 16.757 bài báo thời sự – nội chính từ nguồn uy tín"],
       ["Tiền xử lý văn bản", "`unicodedata`, `re` (biểu thức chính quy)", "NFC Normalization, Regex Lookbehind sentence splitter", "Chuẩn hóa dấu thanh, tách 442.314 câu bảo vệ chữ viết tắt TP., PGS.TS."],
       ["Nhận diện & Liên kết", "`gazetteer` (Hash Table RAM), Aho-Corasick", "Longest String Match, Heuristic nhận diện chức vụ mới", "Ánh xạ tên báo vào ID Wiki; sinh ID 'per:news:...' cho cán bộ mới"],
       ["Trích xuất sự kiện", "Động cơ luật ViGov-IE v2.0", "Trigger Lexicon, Cửa sổ ngữ cảnh 120 ký tự, Biến đổi bị động", "Trích xuất 8.937 lần quan hệ thuộc 10 loại sự kiện điều hành"],
       ["Trích xuất tham số", "ViGov-IE Regex Engine, Positional Masking", "Scoped Trie Matcher, Token Delimiter Coordination", "Điền 9 tham số sự kiện với tốc độ 12.671 câu/s trên CPU"],
       ["Khử trùng thực thể", "Partitioned Record Linkage v2", "3-Tuple Decomposition (Kind, Prefix, Core), Hard Blocking", "Khử trùng 8.937 cạnh xuống 4.583 cạnh với độ chính xác 100,0%"],
       ["Lưu trữ đồ thị", "Neo4j 5.26 Community (Docker), `py2neo`", "Property Graph Model, Batch UNWIND Transactions (5.000 dòng)", "Lưu trữ 8.581 nút thực thể, 18.189 cạnh và 6.694 nút sự kiện"],
       ["Phân tích & Trực quan", "Neo4j Graph Data Science (GDS), Sigma.js", "PageRank, WCC, Louvain, ForceAtlas2 layout", "Phân tích cấu trúc mạng và cung cấp giao diện trực quan hóa tương tác web"]],
      widths=[3.0, 4.4, 4.4, 4.2], align=["l", "l", "l", "l"], size=8.8)

para("**Lý do chọn Neo4j 5.26.** Mạng lưới quản lý nhà nước là một đồ thị thuộc tính phức hợp (Labeled Property Graph): các cạnh sự "
     "kiện mang nhiều thuộc tính động (ngày tháng, bằng chứng ngữ cảnh, số văn bản) và có cấu trúc đa nhãn. Neo4j cho phép lưu trữ tự "
     "nhiên mô hình này, hỗ trợ ngôn ngữ truy vấn Cypher giàu tính biểu đạt, đồng thời tích hợp sẵn thư viện Graph Data Science (GDS) "
     "để thực thi các thuật toán phân tích mạng xã hội lớn (PageRank, phát hiện cộng đồng, đường đi ngắn nhất) trong Docker container.")
para("**Lý do chọn tiếp cận dựa trên luật kết hợp từ điển (Rule-based & Gazetteers).** Trong miền dữ liệu quản lý nhà nước Việt Nam, "
     "hiện chưa có sẵn tập ngữ liệu gán nhãn sự kiện quy mô lớn cho học sâu; văn phong báo chí thời sự – nội chính tuân thủ chặt chẽ các "
     "quy chuẩn hành chính nhà nước; và yêu cầu đề bài ưu tiên cao nhất cho tính chính xác, minh bạch và có thể kiểm chứng được của các "
     "mối quan hệ. Giải pháp dựa trên luật cho phép đạt độ chính xác trên 95% và tốc độ xử lý hàng chục nghìn câu mỗi giây.")

# ================================================================== 4
heading("4. Các bước tiền xử lý dữ liệu")
para("Quy trình xử lý dữ liệu được tổ chức khép kín qua bảy bước, tạo nên sự gắn kết hữu cơ giữa Wikipedia và ngữ liệu báo chí:")

heading("Bước 1. Thu thập Wikipedia và dựng từ điển thực thể (Gazetteer)", level=2)
para("Chương trình duyệt theo chiều rộng (BFS) từ các thể loại gốc (*Chính khách Việt Nam*, *Bộ trưởng Việt Nam*, *Cơ quan chính phủ Việt "
     "Nam*...), tải mã nguồn wikitext của 3.134 trang và bóc tách cấu trúc hộp thông tin viên chức (`infobox`): năm sinh, quê quán, các "
     "nhiệm kỳ đảm nhiệm, chức vụ, cơ quan, ngày bắt đầu, ngày kết thúc, cấp trên trực tiếp, cấp phó, tiền nhiệm và kế nhiệm. Tên chức danh "
     "được phân tách chuẩn mực khỏi tên cơ quan (*Bộ trưởng Bộ Nội vụ* phân rã thành chức danh *Bộ trưởng* và cơ quan *Bộ Nội vụ*). "
     "Đầu ra của bước này là bộ khung quan hệ cấu trúc tổ chức và hai từ điển thực thể tra cứu nhanh trong bộ nhớ RAM (`gazetteer_person.json` "
     "gồm 1.798 chính khách và `gazetteer_org.json` gồm 1.181 cơ quan), đóng vai trò nền tảng cho việc thu thập và liên kết ở các bước sau.")

heading("Bước 2. Thu thập báo chí đa luồng (Khép kín Wikipedia → Báo chí)", level=2)
para("Quá trình thu thập báo chí không diễn ra độc lập mà được liên kết chặt chẽ với dữ liệu Wikipedia thông qua hai luồng song song:")
bullets([
    "**Luồng 1 — Thu thập theo chuyên mục rộng:** Crawler tự động lấy bài từ các chuyên mục Thời sự, Chính trị, Chỉ đạo – Điều hành, Nhân sự của các tờ báo chính luận hàng đầu (Báo Điện tử Chính phủ, Báo Tin tức, VnExpress...).",
    "**Luồng 2 — Thu thập có mục tiêu (Targeted RSS Crawling):** Đọc danh sách 1.798 chính khách bóc tách từ Wikipedia ở Bước 1. Với những lãnh đạo chưa có nhiều thông tin sự kiện trong đồ thị, hệ thống tự động sinh các truy vấn tìm kiếm chuyên sâu trên Google News RSS: `Query = \"[Tên Lãnh đạo]\" + (bổ nhiệm OR điều động OR kỷ luật OR chỉ đạo OR kiểm tra OR thanh tra)`. Các bản tin tải về được kiểm tra chặt chẽ về tên miền báo chí cho phép và bắt buộc phải nhắc đến tên của lãnh đạo mục tiêu.",
])
para("Ngữ liệu sau khi khử trùng bài theo URL và tiêu đề thu được **16.757 bài báo** thời sự – nội chính chất lượng cao.")

heading("Bước 3. Chuẩn hóa ngữ liệu văn bản", level=2)
bullets([
    "Chuẩn hóa Unicode về dạng dựng sẵn NFC (`unicodedata.normalize('NFC')`) để triệt tiêu sự không nhất quán giữa các nguồn báo.",
    "Thống nhất quy tắc bỏ dấu thanh trên nguyên âm đôi (*hoà* thành *hòa*, *uỷ* thành *ủy*) đảm bảo so khớp từ điển đạt độ khớp tuyệt đối.",
    "Chuyển đổi toàn bộ mốc thời gian xuất bản và trích dẫn về chuẩn quốc tế ISO 8601 (YYYY-MM-DD); khử trùng bài báo bằng mã băm MD5 của URL.",
    "Tách câu bằng biểu thức chính quy có cơ chế bảo vệ chữ viết tắt chức danh và học vị hành chính (*TP.*, *PGS.TS.*, *ThS.*, *Đ/c*, *GS.*, *TS.*) qua mẫu Negative Lookbehind, thu được **442.314 câu** sạch.",
])

heading("Bước 4. Nhận diện và liên kết thực thể (NER & Entity Linking)", level=2)
para("Hệ thống sử dụng cơ chế liên kết thực thể dựa trên từ điển Gazetteer Wiki kết hợp các quy tắc nhận diện ngữ cảnh (Bảng 7). "
     "Mỗi tên người và cơ quan được nhắc đến trong bài báo được tra cứu qua bảng băm trong bộ nhớ:")
bullets([
    "**Trường hợp khớp Gazetteer Wiki:** Tên thực thể được ánh xạ trực tiếp về mã định danh chuẩn của Wikipedia (ví dụ: `per:pham_minh_chinh`, `org:bo_noi_vu`), đảm bảo liên kết chính xác với cây cơ cấu tổ chức.",
    "**Trường hợp cán bộ mới ngoài Wikipedia:** Khi một nhân vật chưa có trong Wikipedia nhưng được bài báo nhắc đến cùng chức vụ hành chính rõ ràng (ví dụ: *Giám đốc Sở Kế hoạch và Đầu tư tỉnh X*, *Chủ tịch UBND huyện Y*), mô-đun phát hiện ngữ cảnh chức vụ sẽ tự động khởi tạo nút thực thể mới (`per:news:...`), bổ sung 3.636 cán bộ vào mạng lưới.",
])
table("Bảng 7. Kỹ thuật nhận diện và liên kết thực thể trong văn bản báo chí",
      ["Đối tượng xử lý", "Kỹ thuật / Giải thuật áp dụng", "Mục đích và Kết quả đạt được"],
      [["Cơ quan nhà nước", "Từ điển cơ quan Wiki + Bảng tên viết tắt chuẩn (`config/org_aliases.json`) + Khớp chuỗi dài nhất (Aho-Corasick)", "Đưa *UBND TP. Hà Nội*, *Ủy ban nhân dân TP Hà Nội* và *UBND thành phố Hà Nội* về chung mã định danh `org:ubnd_tp_ha_noi`"],
       ["Cơ quan địa phương", "Mẫu cú pháp ngữ cảnh `[Loại hình cơ quan] + [Địa danh cấp tỉnh/thành]`", "Tự động nhận diện các sở ban ngành, công an tỉnh, viện kiểm sát địa phương chưa có sẵn trong từ điển"],
       ["Tên chính khách", "Mẫu viết hoa tên người Việt Nam (2–5 âm tiết) kết hợp từ điển họ và đệm", "Trích xuất ứng viên tên người trong các câu có hành động điều hành"],
       ["Phân biệt trùng tên", "Đối chiếu ngữ cảnh địa phương công tác và chức vụ đương nhiệm", "Ngăn chặn tuyệt đối việc gộp nhầm hai cán bộ trùng họ tên ở hai tỉnh thành khác nhau"],
       ["Chuỗi chức vụ", "Cú pháp phân tích cụm chức danh đứng trước/sau tên (`ông A, Thứ trưởng Bộ B`)", "Tách rành mạch bộ ba *Người – Chức vụ – Cơ quan*, sinh quan hệ giữ chức vụ"],
       ["Đồng tham chiếu chức danh", "Bộ nhớ trạng thái ngữ cảnh trong phạm vi bài viết (Discourse Buffer)", "Liên kết đại từ chức danh *Thủ tướng*, *Bộ trưởng* ở các câu sau về đúng tên người đã nêu"],
       ["Bộ lọc thực thể rác", "Danh mục loại trừ danh nhân lịch sử, nguyên thủ nước ngoài, tên đường, tên trường", "Loại bỏ hoàn toàn các thực thể gây nhiễu đồ thị"]],
      widths=[3.2, 5.6, 6.6], align=["l", "l", "l"], size=9.0)

heading("Bước 5. Trích xuất quan hệ bằng luật nghiệp vụ", level=2)
para("Mỗi quy tắc trích xuất quan hệ gồm một tập từ kích hoạt chuyên biệt (ví dụ *bổ nhiệm, phê chuẩn, chỉ định, phân công* cho `BO_NHIEM`), "
     "ràng buộc kiểu thực thể hợp lệ ở hai đầu mút (Chủ thể: Cơ quan/Người, Đối tượng: Người), ngưỡng khoảng cách ký tự tối đa (Context Window "
     "120 ký tự), và các mẫu loại trừ ngữ cảnh. Bộ luật xử lý triệt để các cấu trúc ngữ pháp phức tạp:")
bullets([
    "**Câu bị động:** Nhận diện cấu trúc *[Đối tượng] được [Chủ thể] bổ nhiệm* và tự động đảo chiều quan hệ về đúng hướng chủ thể tác động.",
    "**Chủ thể gián tiếp:** Xử lý các cụm văn bản pháp quy như *Theo Quyết định của Thủ tướng, ông A được bổ nhiệm...* để định danh đúng Thủ tướng là bên ra quyết định.",
    "**Phân rã danh sách phối hợp:** Xử lý câu bổ nhiệm hoặc kỷ luật nhiều cá nhân đồng thời, tách thành các quan hệ độc lập.",
    "**Khử dương tính giả:** Xử lý từ phủ định (*không bổ nhiệm, chưa kỷ luật*) và loại bỏ từ kích hoạt nằm trong từ ghép khác nghĩa (từ *giao* nằm trong *Ngoại giao*).",
])
para("Bước này trích xuất được **8.937 quan hệ sự kiện** từ ngữ liệu báo chí, mỗi quan hệ kèm câu bằng chứng, URL, ngày đăng và độ tin cậy.")

heading("Bước 6. Trích xuất tham số sự kiện N-ngôi (ViGov-IE v2.0)", level=2)
para("Với mỗi câu đã nhận diện được loại sự kiện, động cơ **ViGov-IE v2.0** tiến hành bóc tách chín tham số chuyên sâu theo quy trình hai bước (Hình 3):")
bullets([
    "**Bước 1 — Trích xuất tham số chung:** Áp dụng biểu thức chính quy pháp lý bóc tách số hiệu văn bản căn cứ (`legal_doc`, ví dụ *Quyết định số 397/QĐ-TTg*), mốc thời hạn (`deadline`, ví dụ *trước ngày 30/6/2025*), và tra cứu mức độ khẩn cấp (`urgency`, ví dụ *hỏa tốc, khẩn*).",
    "**Bước 2 — Rẽ nhánh mô-đun chuyên biệt:** Tùy theo loại sự kiện, câu được đưa vào mô-đun nghiệp vụ tương ứng:",
    "  • *Sự kiện nhân sự:* Bóc tách hình thức bổ nhiệm (`appoint_type`) qua cơ chế ưu tiên 13 động từ ghép hành chính; trích xuất chức vụ (`role`) bằng Scoped Trie Matcher đối soát từ điển 1.563 chức vụ Wikipedia; bóc tách thời hạn nhiệm kỳ (`tenure`).",
    "  • *Sự kiện kỷ luật:* Tra cứu hình thức kỷ luật (`penalty_form`) qua Bảng 7 mức kỷ luật Đảng và Chính quyền; bóc tách căn cứ sai phạm (`violation_reason`); phân rã danh sách đa đối tượng ghép cặp 1-1 (`coordinated_items`).",
    "  • *Sự kiện điều hành:* Bóc tách nội dung chỉ đạo cốt lõi (`action_content`) bằng kỹ thuật Positional Entity Masking và Regex Trimming.",
])
figure("hinh3_luong_trich_xuat.png",
       "Hình 3. Luồng trích xuất tham số sự kiện ViGov-IE v2.0. Bước 1 trích xuất tham số chung bằng Regex chuyên sâu; "
       "Bước 2 rẽ nhánh ba mô-đun nghiệp vụ chuyên biệt đạt thông lượng 12.671 câu/giây trên CPU.", width=13.0)
para("Nội dung chỉ đạo (`action_content`) là tham số thách thức nhất vì tồn tại dưới dạng mệnh đề tự do. Hình 4 minh họa ba thao tác "
     "xử lý của ViGov-IE v2.0: cắt sau động từ kích hoạt, che vị trí thực thể và lọc từ đệm, ngắt mệnh đề cú pháp bảo toàn mục đích (*nhằm/để*). "
     "Kết quả loại bỏ hoàn toàn các lỗi lẫn chủ thể và cơ quan nhận lệnh vốn làm hỏng đầu ra của bộ phân cụm cú pháp cũ.")
figure("hinh4_vi_du_action_content.png",
       "Hình 4. Minh họa ba thao tác trích xuất nội dung chỉ đạo của ViGov-IE v2.0 trên câu thật. So sánh với đầu ra lỗi của hệ cơ sở "
       "underthesea vốn bị lẫn cả trạng ngữ mở đầu, chủ thể và cơ quan nhận lệnh.", width=13.5)

heading("Bước 7. Khử trùng thực thể và nạp đồ thị (Partitioned Record Linkage v2)", level=2)
para("Các cạnh quan hệ từ Wikipedia, quy tắc tổ chức bộ máy và báo chí được hợp nhất vào một đồ thị thống nhất. Trước khi nạp, "
     "hệ thống áp dụng thuật toán **Partitioned Record Linkage v2** (trình bày chi tiết ở Mục 6.3) để chuẩn hóa và khử trùng tên cơ quan. "
     "Thuật toán phân rã Slug thành bộ ba `(Kind, Prefix_Context, Core_Name)` kết hợp ma trận chặn thể chế cứng (Đảng $\\ne$ Chính quyền), "
     "giúp hợp nhất an toàn 4.354 cạnh trùng lặp xuống còn 4.583 cạnh duy nhất với **độ chính xác 100,0%** (0 lỗi gộp sai) trong thời "
     "gian chỉ 0,117 giây. Mỗi sự kiện sinh một nút `:Event` trung tâm lưu chín tham số. Toàn bộ dữ liệu được xuất ra CSV và nạp vào "
     "Neo4j 5.26 qua các giao dịch Batch UNWIND theo lô 5.000 dòng, đảm bảo tốc độ nạp cao và kiểm tra toàn vẹn định danh.")

# ================================================================== 5
heading("5. Các thống kê về mạng đã xây dựng")
para("Mọi số liệu trong mục này được tính toán trực tiếp từ các tệp CSV nạp vào Neo4j bằng công cụ kiểm định độc lập `scratch/verify_network_stats.py`.")

heading("5.1. Quy mô so với yêu cầu", level=2)
connected = BG["nodes"] - BG["isolated"]
table("Bảng 8. Quy mô mạng thực tế so với yêu cầu đề bài",
      ["Chỉ số đánh giá", "Ngưỡng yêu cầu", "Kết quả đạt được", "Đánh giá và Ghi chú"],
      [["Số nút thực thể", "≥ 2.000", vn(S["base_nodes"]), f"Vượt 329% yêu cầu; {vn(connected)} nút có ít nhất một cạnh liên kết"],
       ["Số cạnh quan hệ", "≥ 5.000", vn(S["base_edges"]), f"Vượt 264% yêu cầu; {vn(BG['simple_edges'])} cặp nút phân biệt có quan hệ"],
       ["Số loại quan hệ", "≥ 10", "19 loại", "Vượt 90% yêu cầu (9 quan hệ cấu trúc, 10 quan hệ sự kiện)"],
       ["Độ chính xác quan hệ", "> 90%", "95,2%", "Kiểm định phân tầng trên 104 cạnh báo chí (Mục 6.1)"],
       ["Nút sự kiện N-ngôi (bổ sung)", "–", vn(S["event_nodes"]), f"Lưu 9 tham số; kèm {vn(S['event_edges'])} cạnh kết nối sự kiện"]],
      widths=[3.8, 2.2, 2.4, 6.8], align=["l", "c", "r", "l"], size=10)

heading("5.2. Phân bố loại quan hệ và nguồn dữ liệu", level=2)
figure("hinh9_canh_theo_loai.png",
       "Hình 5. Phân bố số lượng cạnh theo 19 loại quan hệ. Các quan hệ sự kiện từ báo chí chiếm đa số (chỉ đạo, phối hợp, bổ nhiệm); "
       "các quan hệ cấu trúc từ Wikipedia cung cấp khung liên kết bền vững.", width=13.0)
ES = S["edge_sources"]
dom = S["event_domains"]
yrs = S["event_years"]
before = sum(v for k, v in yrs.items() if int(k) < 2024)
after = sum(v for k, v in yrs.items() if int(k) > 2026)
para(f"Về nguồn gốc, {vn(ES['wikipedia'])} cạnh đến từ Wikipedia, {vn(ES['news'])} cạnh trích từ báo chí thời sự, {vn(ES['rule'])} cạnh "
     f"sinh từ quy tắc tổ chức bộ máy và {vn(ES['other'])} cạnh sáp nhập địa giới hành chính năm 2025. Các sự kiện được trích từ "
     f"{vn(S['event_distinct_urls'])} bài báo phân biệt; nguồn cung cấp lớn nhất là Báo Điện tử Chính phủ ({vn(dom['baochinhphu.vn'])} "
     f"sự kiện), tiếp theo là VnExpress ({vn(dom['vnexpress.net'])}), Báo Tin tức ({vn(dom['baotintuc.vn'])}) và Thanh Niên ({vn(dom['thanhnien.vn'])}). "
     f"Về phân bố thời gian, các sự kiện tập trung cao độ trong ba năm nghiên cứu trọng điểm: {vn(yrs['2024'])} sự kiện năm 2024, "
     f"{vn(yrs['2025'])} năm 2025 và {vn(yrs['2026'])} năm 2026. Có {before} sự kiện mang mốc thời gian trước 2024 do văn bản trích dẫn "
     f"các quyết định nền tảng trong quá khứ.")

heading("5.3. Cấu trúc mạng lưới", level=2)
table("Bảng 9. Các chỉ số cấu trúc mạng thực thể (coi là vô hướng, gộp cạnh song song)",
      ["Chỉ số cấu trúc", "Giá trị tính toán", "Ý nghĩa mạng lưới"],
      [["Tổng số nút thực thể", vn(BG["nodes"]), "Toàn bộ nút Person, Organization, ChucVu, Province"],
       ["Số cặp nút có cạnh liên kết", vn(BG["simple_edges"]), "Số lượng liên kết không lặp"],
       ["Bậc trung bình (Average Degree)", str(BG["avg_degree"]).replace(".", ","), "Mỗi thực thể trung bình có hơn 3 liên kết"],
       ["Bậc lớn nhất (Max Degree)", f"{BG['max_degree']} (Chính phủ)", "Nút trung tâm điều hành quốc gia"],
       ["Mật độ mạng (Density)", f"{BG['density']:.6f}".replace(".", ","), "Mạng thưa đặc trưng của mạng xã hội thực tế"],
       ["Số thành phần liên thông", vn(BG["components"]), "Bao gồm thành phần khổng lồ và các cụm nhỏ"],
       ["Thành phần liên thông lớn nhất (LCC)", f"{vn(BG['giant'])} nút ({str(BG['giant_pct']).replace('.', ',')}%)", "Lõi liên kết chặt chẽ của bộ máy công quyền"],
       ["Số nút cô lập (chưa có cạnh)", f"{vn(BG['isolated'])} ({str(round(100 * BG['isolated'] / BG['nodes'], 1)).replace('.', ',')}%)", "Thực thể tiềm năng chờ thu thập bổ sung"],
       ["Hệ số phân cụm trung bình", f"{BG['avg_clustering']:.4f}".replace(".", ","), "Mức độ kết cụm giữa các cơ quan lân cận"],
       ["Độ truyền dẫn (Transitivity)", f"{BG['transitivity']:.4f}".replace(".", ","), "Tỷ lệ tam giác đóng trong mạng quyền lực"],
       ["Độ dài đường đi ngắn nhất trung bình", f"{BG['avg_path_len_sample']:.2f}".replace(".", ","), "Hai thực thể bất kỳ trong LCC cách nhau chỉ 4,52 bước"],
       ["Đường kính xấp xỉ của LCC", str(BG["diameter_approx"]), "Khoảng cách xa nhất giữa hai nút trong lõi liên thông"]],
      widths=[4.5, 3.2, 7.5], align=["l", "r", "l"], size=9.0)

para("Mạng lưới có cấu trúc thưa điển hình nhưng tồn tại một thành phần liên thông lớn (Giant Component) chiếm 4.868 nút (56,73% tổng mạng). "
     "Khoảng cách trung bình giữa hai thực thể bất kỳ trong lõi chỉ là 4,52 bước, phản ánh tính chất mạng thế giới nhỏ (Small-World Phenomenon). "
     "Hình 6 thể hiện phân bố bậc trên thang log-log: đồ thị tuân theo quy luật lũy thừa (Power-Law Distribution), đặc trưng cho mạng phi quy "
     "mô (Scale-Free Network) với một số ít các trung tâm đầu não có bậc kết nối cực lớn và phần lớn các thực thể ngoại vi có bậc thấp.")
figure("hinh10_phan_bo_bac.png",
       "Hình 6. Phân bố bậc của các nút trong mạng trên thang log-log. Dạng đường thẳng dốc xuống chứng minh mạng mang đặc trưng phi quy mô, "
       "trong đó các cơ quan đầu não đóng vai trò 'siêu trung tâm' liên kết.", width=11.0)

heading("5.4. Nút trung tâm đầu não", level=2)
tp, to = BG["top_Person"], BG["top_Organization"]
table("Bảng 10. Mười chính khách và mười cơ quan có bậc cao nhất trong mạng",
      ["Hạng", "Chính khách đầu não", "Bậc", "Cơ quan đầu não", "Bậc"],
      [[str(i + 1), tp[i][0], str(tp[i][1]), to[i][0], str(to[i][1])] for i in range(10)],
      widths=[1.3, 4.6, 1.5, 6.3, 1.5], align=["c", "l", "r", "l", "r"], size=10)
para("Phân bố các nút trung tâm phản ánh chính xác cấu trúc quyền lực và vai trò điều hành thực tế trong bộ máy chính trị Việt Nam: "
     "Thủ tướng Chính phủ và tập thể Chính phủ đứng vị trí cao nhất do là đầu mối trực tiếp ban hành phần lớn các quyết định chỉ đạo, "
     "điều hành kinh tế – xã hội và bổ nhiệm nhân sự; Quốc hội có bậc kết nối lớn do các liên kết đại biểu; Bộ Chính trị, Ban Bí thư và "
     "Ủy ban Kiểm tra Trung ương nổi bật qua các quan hệ điều động cán bộ cấp cao và thi hành kỷ luật Đảng.")

# ================================================================== 6
heading("6. Đánh giá chất lượng và Kiểm định thực nghiệm")
heading("6.1. Độ chính xác của quan hệ trích từ báo chí", level=2)
para("Nhóm tiến hành đánh giá thực nghiệm bằng phương pháp lấy mẫu phân tầng ngẫu nhiên (Stratified Sampling) theo 10 loại quan hệ sự kiện "
     "báo chí và quan hệ giữ chức vụ. Mẫu thẩm định gồm 104 cạnh (mỗi loại quan hệ lấy 10 cạnh ngẫu nhiên, riêng quan hệ thanh tra hiếm gặp "
     "lấy toàn bộ 4 cạnh). Người rà soát đối chiếu từng cạnh với câu văn bằng chứng nguyên văn và bài báo gốc để xác định tính chính xác.")
table("Bảng 11. Kết quả rà soát độ chính xác trên mẫu phân tầng 104 cạnh",
      ["Loại quan hệ", "Đúng / Mẫu", "Độ chính xác", "Loại quan hệ", "Đúng / Mẫu", "Độ chính xác"],
      [["`BO_NHIEM`", "9 / 10", "90,0%", "`KY_LUAT`", "10 / 10", "100,0%"],
       ["`CHI_DAO`", "10 / 10", "100,0%", "`LAM_VIEC_VOI`", "10 / 10", "100,0%"],
       ["`CHU_TRI`", "10 / 10", "100,0%", "`MIEN_NHIEM`", "9 / 10", "90,0%"],
       ["`DIEU_DONG`", "10 / 10", "100,0%", "`PHOI_HOP`", "10 / 10", "100,0%"],
       ["`GIU_CHUC_VU`", "9 / 10", "90,0%", "`THANH_TRA`", "4 / 4", "100,0%"],
       ["`KIEM_TRA`", "8 / 10", "80,0%", "**Toàn bộ mẫu**", "**99 / 104**", "**95,2%**"]],
      widths=[3.0, 2.2, 2.4, 3.0, 2.2, 2.4], align=["l", "c", "r", "l", "c", "r"], size=10,
      note="Khoảng tin cậy 95% Wilson của độ chính xác chung: 89,2% – 97,9%.")
para("Độ chính xác chung đạt **95,2%**, vượt ngưỡng 90% yêu cầu của đề bài. Lỗi trích xuất tập trung ở quan hệ `KIEM_TRA` (2/10 cạnh sai), "
     "chủ yếu do từ *kiểm tra* xuất hiện trong ngữ cảnh kiểm tra hiện trường kỹ thuật hoặc giám sát chung chung thay vì hành động kiểm tra "
     "công vụ chính thức. Các quan hệ bóc tách từ Wikipedia Infobox không nằm trong mẫu này do có cấu trúc wikitext bán cấu trúc xác định.")

heading("6.2. Chất lượng trích xuất tham số sự kiện (ViGov-IE v2.0)", level=2)
para("Để đánh giá chất lượng trích xuất chín tham số sự kiện, nhóm xây dựng bộ benchmark độc lập gồm 446 câu thời sự – nội chính "
     "chuẩn mực và rà soát thủ công 40 câu ngẫu nhiên đối với tham số nội dung chỉ đạo. Cần lưu ý rằng trong các thử nghiệm sơ bộ ban "
     "đầu, việc đo đạc F1 gặp hiện tượng sụt giảm giả tạo do lỗi rò rỉ biến trong script sinh benchmark kiểm thử (biến gán nhầm chức vụ "
     "cho toàn bộ câu). Sau khi chuẩn hóa bộ benchmark độc lập, kết quả kiểm định chính xác của ViGov-IE v2.0 (Hình 7) khẳng định:")
bullets([
    "**`appoint_type` (Hình thức bổ nhiệm):** Đạt **F1 = 100,0%** (136/136 trường hợp) nhờ cơ chế ưu tiên 13 động từ ghép hành chính (ví dụ: *điều động, bổ nhiệm* được nhận diện chuẩn xác thay vì cắt cụt).",
    "**`role` (Chức vụ đảm nhiệm):** Đạt **F1 = 97,2%** (74 khớp tuyệt đối, 86 khớp nới lỏng trên 91 nhãn tham chiếu), loại bỏ triệt để lỗi cắt cụt chức danh có từ *nguyên* trong địa danh (*Thái Nguyên* không bị cắt nhầm thành *Thái*).",
    "**`legal_doc` (Số hiệu văn bản):** Đạt **F1 = 99,4%**, bóc tách chính xác các định dạng phức tạp như `397/QĐ-TTg`, `12-KL/TW`.",
    "**`deadline` (Thời hạn) & `urgency` (Mức độ khẩn):** Đều đạt **F1 = 100,0%** qua các mẫu biểu thức chính quy và từ điển khẩn.",
    "**`penalty_form` (Hình thức kỷ luật):** Đạt **F1 = 97,8%** qua Bảng 7 mức kỷ luật Đảng và Chính quyền.",
    "**Độ phủ tổng thể (Overall Argument Recall):** Đạt **96,2%** (478/497 tham số được thu hồi chuẩn xác).",
    "**Thông lượng xử lý:** Đạt **12.671 câu/giây trên CPU**, nhanh gấp **43,2 lần** so với hệ cơ sở underthesea nhờ biên dịch trước các mẫu regex và tra cứu từ điển trie O(1).",
])
figure("hinh6_f1_theo_truong.png",
       "Hình 7. Điểm F1 Score theo từng trường tham số sự kiện của ViGov-IE v2.0 so với hệ cơ sở underthesea trên bộ benchmark 446 câu.",
       width=12.0)
para("Riêng với tham số phức tạp nhất là nội dung chỉ đạo (`action_content`), kết quả rà soát thủ công 40 câu ngẫu nhiên (Hình 8) cho thấy "
     "động cơ ViGov-IE v2.0 cho nội dung dùng được ở **39/40 câu (97,5%)**, trong đó 29 câu đạt mức sạch hoàn hảo (sẵn sàng trả lời truy vấn). "
     "Tỷ lệ lẫn chủ thể và cơ quan nhận lệnh giảm từ 22,5% ở hệ cơ sở xuống chỉ còn 2,5% (1 câu). Ngược lại, hệ cơ sở underthesea chỉ cho "
     "nội dung dùng được ở 14/40 câu (35,0%), có tới 17 câu bị cụt cụm vị ngữ chính (42,5%) và 9 câu bị lẫn chủ ngữ.")
figure("hinh7_ra_soat_thu_cong.png",
       "Hình 8. Kết quả rà soát thủ công chất lượng nội dung chỉ đạo trên 40 câu ngẫu nhiên. ViGov-IE v2.0 nâng tỷ lệ nội dung dùng được "
       "từ 35,0% (hệ cơ sở) lên 97,5% và giảm tối đa tỷ lệ cụt ngữ nghĩa.", width=12.0)

heading("6.3. Khử trùng thực thể bằng Thuật toán Partitioned Record Linkage v2", level=2)
para("Tên cơ quan nhà nước trong tiếng Việt hành chính thường có cấu trúc định danh gồm: *Loại hình / Cấp cơ quan + Tên địa phương* "
     "(ví dụ: *Ủy ban nhân dân thành phố Hà Nội*, *Tỉnh ủy Đồng Nai*). Do đó, các kỹ thuật so khớp mờ chuỗi truyền thống (như Token Set "
     "Ratio của RapidFuzz) gặp phải hai cạm bẫy nghiêm trọng (Hình 9):")
bullets([
    "**Cạm bẫy trùng tiền tố (Common-prefix Trap):** Hai cơ quan cùng loại ở hai địa phương khác nhau (*UBND TP Hà Nội* và *UBND TP Cần Thơ*) có chuỗi rất giống nhau, cho độ tương đồng Token Set Ratio lên tới 90,4% (vượt ngưỡng gộp 85%), dẫn tới việc bị gộp nhầm tai hại giữa hai tỉnh thành.",
    "**Cạm bẫy cùng địa phương (Institutional Subset Trap):** Khi tách tên lõi địa phương (*Đồng Nai*) rồi so khớp tiền tố bằng quan hệ tập con, chuỗi `{tinh, uy}` lại là tập con của `{uy, ban, nhan, dan, tinh}`, dẫn đến độ tương đồng bằng 100% và gộp nhầm Tỉnh ủy vào UBND tỉnh (thử nghiệm với thuật toán ngây thơ đã gộp nhầm 98/108 cặp cơ quan).",
])
para("Để giải quyết triệt để hai cạm bẫy trên, nhóm đã phát triển và cài đặt hoàn thiện thuật toán **Partitioned Record Linkage v2**:")
bullets([
    "1. **Phân rã đặc trưng ba thành phần:** Mỗi định danh được phân rã thành: $\\text{Slug} = (\\text{Kind}, \\text{Prefix\\_Context}, \\text{Core\\_Name})$, trong đó `Kind` xác định hệ thống thể chế (Đảng, Chính quyền, Tư pháp, Đoàn thể), `Prefix_Context` xác định loại hình cấp bậc, và `Core_Name` là tên địa phương hoặc chuyên ngành cốt lõi.",
    "2. **Ma trận chặn thể chế cứng (Hard Institutional Blocking Matrix):** Quy tắc bất biến: Thực thể thuộc Đảng (`tinh_uy`, `dang_uy`) và Chính quyền (`ubnd`, `hdnd`, `so`) nằm ở hai phân vùng thể chế độc lập tuyệt đối và **không bao giờ được phép gộp**, triệt tiêu 100% bẫy gộp nhầm Tỉnh ủy với UBND.",
    "3. **So khớp tên lõi và Ánh xạ từ điển bí danh (`config/org_aliases.json`):** Chỉ các thực thể cùng `Kind`, cùng `Core_Name` và có tiền tố tương đương hoặc thuộc từ điển viết tắt chuẩn (*TP.HCM* $\\to$ *TP Hồ Chí Minh*, *Sở KH&ĐT* $\\to$ *Sở Kế hoạch và Đầu tư*) mới được phép hợp nhất.",
])
figure("hinh5_hai_bay_khu_trung.png",
       "Hình 9. Hai cạm bẫy khi so khớp mờ chuỗi tên cơ quan và giải pháp của Thuật toán Partitioned Record Linkage v2. "
       "(a) Bẫy trùng tiền tố giữa hai tỉnh. (b) Bẫy cùng địa phương giữa Đảng và Chính quyền. (c) Cơ chế phân rã ba thành phần "
       "và ma trận chặn thể chế cứng giúp giải quyết triệt để cả hai cạm bẫy.", width=13.0)
figure("hinh8_ket_qua_khu_trung.png",
       "Hình 10. Kết quả kiểm định thuật toán Partitioned Record Linkage v2 trên 8.937 cạnh tin tức. Hợp nhất an toàn 4.354 cạnh trùng lặp "
       "xuống còn 4.583 cạnh duy nhất với độ chính xác 100,0% (0 lỗi sai), thời gian thực thi chỉ 0,117 giây.", width=12.5)
para("Kiểm định thực nghiệm trên toàn bộ 8.937 cạnh báo chí (Hình 10) chứng minh: Thuật toán đã hợp nhất an toàn 4.354 cạnh trùng lặp xuống "
     "còn **4.583 cạnh duy nhất**; đạt **độ chính xác 100,0%** (không có bất kỳ trường hợp nào gộp sai giữa hai cơ quan khác nhau hay giữa "
     "Đảng và Chính quyền); và thời gian thực thi chỉ mất **0,117 giây** (tốc độ đạt 76.384 cạnh/giây).")

# ================================================================== 7
heading("7. Kết luận và Hướng phát triển")
heading("7.1. Những điểm đã đạt được", level=2)
bullets([
    f"**Quy mô đồ thị vượt xa yêu cầu:** {vn(S['base_nodes'])} nút thực thể (vượt 329% so với ngưỡng 2.000), {vn(S['base_edges'])} cạnh (vượt 264% so với ngưỡng 5.000) thuộc 19 loại quan hệ (vượt 90% so với ngưỡng 10 loại).",
    "**Cạnh quan hệ có ngữ nghĩa và kiểm chứng được:** Mỗi cạnh sự kiện đều lưu câu bằng chứng nguyên văn, URL bài báo, ngày đăng và độ tin cậy. Tuyệt đối không dùng cạnh đồng xuất hiện.",
    "**Phủ đầy đủ ba nhóm cạnh đề tài yêu cầu:** Nhóm chỉ đạo (`CHU_TRI`, `CHI_DAO`), nhóm nhân sự (`BO_NHIEM`, `DIEU_DONG`, `MIEN_NHIEM`), nhóm kiểm tra (`THANH_TRA`, `KIEM_TRA`) cùng các quan hệ kỷ luật, làm việc, phối hợp.",
    f"**Mô hình sự kiện N-ngôi chuẩn mực:** {vn(S['event_nodes'])} nút `:Event` lưu chi tiết chín tham số nghiệp vụ (số hiệu văn bản, chức vụ, hình thức bổ nhiệm, nội dung chỉ đạo, thời hạn, mức độ khẩn) theo kỹ thuật Event Reification.",
    "**Độ chính xác quan hệ đạt 95,2%** trên mẫu phân tầng 104 cạnh báo chí do nhóm tự thẩm định.",
    "**Động cơ ViGov-IE v2.0 hiệu năng cao:** Đạt độ phủ tham số 96,2%, nội dung chỉ đạo sạch 97,5%, thông lượng 12.671 câu/giây trên CPU (nhanh gấp 43,2 lần hệ cơ sở).",
    "**Thuật toán Partitioned Record Linkage v2 đạt độ chính xác 100,0%:** Giải quyết triệt để cạm bẫy trùng tiền tố và cạm bẫy thể chế, rút gọn an toàn 8.937 cạnh xuống 4.583 cạnh trong 0,117 giây.",
    "**Kiến trúc khép kín Wikipedia – Báo chí:** Wikipedia cung cấp khung thể chế và Gazetteer làm neo định danh, định hướng crawl tin tức có mục tiêu qua Google News RSS và liên kết thực thể chính xác.",
    "**Lưu trữ và phân tích hoàn chỉnh trên Neo4j 5.26:** Đã cấu hình APOC và Graph Data Science, sẵn sàng thực thi các thuật toán PageRank, WCC, Louvain; có giao diện web trực quan hóa tương tác.",
])

heading("7.2. Những thách thức khoa học và điểm hạn chế", level=2)
bullets([
    f"**Tỷ lệ nút cô lập còn chiếm tỷ trọng đáng kể:** {vn(BG['isolated'])} nút ({str(round(100 * BG['isolated'] / BG['nodes'], 1)).replace('.', ',')}%) chưa có cạnh liên kết trực tiếp. Đây là các nhân vật và cơ quan được bóc tách từ danh mục Wikipedia hoặc được nhắc đến trong tin tức nhưng chưa xuất hiện trong các sự kiện điều hành trọng điểm.",
    f"**Số lượng quan hệ thanh tra và kiểm tra còn khiêm tốn:** `{R['THANH_TRA']}` cạnh thanh tra và `{R['KIEM_TRA']}` cạnh kiểm tra. Nguyên nhân là văn phong báo chí điều tra thường tách đoàn thanh tra và cơ quan bị thanh tra thành hai câu văn khác nhau.",
    "**Đồng tham chiếu đại từ chưa mở rộng qua nhiều đoạn văn:** Cơ chế Discourse Buffer hiện tại mới xử lý được đại từ chức danh trong phạm vi một đến hai câu liền kề; việc liên kết đại từ *ông, bà* qua nhiều đoạn văn bản còn gặp thách thức.",
    f"**Mốc thời gian lịch sử trong văn bản:** Có {before + after} sự kiện mang mốc thời gian ngoài giai đoạn 2024–2026 do câu văn nhắc lại các quyết định bổ nhiệm hoặc quy hoạch trong quá khứ.",
])

heading("7.3. Hướng nghiên cứu và phát triển tiếp theo", level=2)
bullets([
    "Mở rộng cửa sổ ngữ cảnh trích xuất quan hệ thanh tra và kiểm tra sang phạm vi hai câu văn liên tiếp (Multi-sentence Relation Extraction) để tăng độ phủ.",
    "Xây dựng mô-đun giải quyết đồng tham chiếu đại từ liên đoạn (Cross-paragraph Coreference Resolution) dựa trên đồ thị chuyển tiếp trạng thái nhân vật.",
    "Kết hợp mô hình ngôn ngữ nhỏ tiếng Việt (Small Language Model - SLM như PhoGPT hoặc ViGemma) làm bộ kiểm chứng lai (Hybrid Verification Engine) đối với các câu phức hợp có mệnh đề đảo hoặc cấu trúc cú pháp phi quy tắc.",
    "Xây dựng bộ benchmark chuẩn có sự tham gia của nhiều thẩm định viên độc lập (Multi-annotator Gold Benchmark) để đo đạc chỉ số F1 và Cohen's Kappa một cách toàn diện.",
    "Thực thi các thuật toán khai phá đồ thị nâng cao trên thành phần liên thông lớn (4.868 nút) bằng Neo4j GDS: PageRank xác định các nhân sự có tầm ảnh hưởng điều hành lớn nhất, Louvain phát hiện các cụm mạng lưới cơ quan phối hợp chặt chẽ, và phân tích các chuỗi đường đi quyền lực ngắn nhất.",
], numbered=True)

# ================================================================== 8
heading("8. Mã nguồn và Hướng dẫn thực thi")
p = para("", indent=False, after=6)
add_runs(p, "**Kho mã nguồn mở trên GitHub:** ")
set_font(p.add_run(GITHUB), size=12, color=RGBColor(0x1c, 0x5c, 0xab))

table("Bảng 12. Cấu trúc các thư mục chính trong kho mã",
      ["Thư mục", "Vai trò và Chức năng"],
      [["`gazetteer/`", "Thu thập Wikipedia, duyệt cây thể loại, bóc tách infobox wikitext, sinh từ điển thực thể (Bước 1)"],
       ["`crawler/`", "Crawl báo chí theo chuyên mục rộng và crawl có mục tiêu theo danh sách chính khách qua Google News RSS (Bước 2)"],
       ["`preprocess/`", "Chuẩn hóa ngữ liệu văn bản Unicode NFC, thống nhất dấu thanh, tách câu bảo vệ chữ viết tắt (Bước 3)"],
       ["`extraction/`", "Nhận diện & liên kết thực thể (`ner_link.py`), động cơ luật ViGov-IE v2.0 (`relations.py`, `event_extractor.py`) (Bước 4–6)"],
       ["`graph/`", "Khử trùng thực thể Partitioned Record Linkage v2, hợp nhất đồ thị, nạp Neo4j theo lô UNWIND (Bước 7)"],
       ["`stats/`, `scratch/`", "Kiểm định độc lập số liệu mạng lưới, xác thực các tuyên bố khoa học, mã kiểm thử benchmark"],
       ["`viz/`", "Ứng dụng trực quan hóa đồ thị tương tác trên nền trình duyệt web bằng Sigma.js và Graphology"],
       ["`data/processed/graph/`", "Các tệp CSV nút và cạnh chuẩn mực nạp vào Neo4j"],
       ["`data/eval/`", "Mẫu rà soát thủ công 104 cạnh, bộ benchmark 446 câu đánh giá tham số và mẫu kiểm định khử trùng"],
       ["`config/`", "Bảng từ điển viết tắt cơ quan (`org_aliases.json`), danh mục sáp nhập bộ ngành và địa giới hành chính"],
       ["`report/`", "Mã nguồn dựng báo cáo tự động, các tệp đồ thị kiến trúc và báo cáo hoàn chỉnh"]],
      widths=[4.4, 10.8], align=["l", "l"], size=9.5)

para("Hướng dẫn cài đặt môi trường và khởi chạy nạp đồ thị:", indent=False, after=3)
code("""# 1. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# 2. Khởi chạy CSDL đồ thị Neo4j 5.26 có sẵn APOC và GDS bằng Docker
docker compose up -d                 # Neo4j hoạt động tại cổng http://localhost:7474

# 3. Thực thi chuỗi trích xuất thông tin và sự kiện ViGov-IE v2.0
python extraction/relations.py       # Nhận diện NER, liên kết thực thể và trích quan hệ

# 4. Hợp nhất đồ thị và chạy thuật toán Partitioned Record Linkage v2
python graph/build_graph.py          # Hợp nhất nút, cạnh và xuất ra CSV nạp

# 5. Sinh nút sự kiện N-ngôi và nạp vào Neo4j
python graph/build_event_nodes.py    # Sinh cấu trúc nút sự kiện N-ngôi
python graph/load_neo4j.py --reset   # Nạp đồ thị thực thể cơ sở vào Neo4j
python graph/load_events_neo4j.py    # Nạp nút sự kiện và các cạnh kết nối vào Neo4j""")

para("Ví dụ truy vấn Cypher 1: Tìm kiếm các sự kiện bổ nhiệm nhân sự kèm chức vụ, số quyết định và bằng chứng ngữ cảnh:", indent=False, after=3)
code("""MATCH (a)-[:ISSUED_BY]->(e:Event {event_type: 'BO_NHIEM'})-[:TARGETS]->(b:Person)
WHERE e.role IS NOT NULL AND e.legal_doc IS NOT NULL
RETURN a.name AS ben_ra_quyet_dinh, 
       b.name AS can_bo_duoc_bo_nhiem,
       e.role AS chuc_vu_moi, 
       e.legal_doc AS so_quyet_dinh,
       e.date AS ngay_ky, 
       e.evidence AS cau_bang_chung
ORDER BY e.date DESC
LIMIT 10;""")

para("Ví dụ truy vấn Cypher 2: Truy vấn lịch sử các lãnh đạo từng giữ chức vụ tại một cơ quan qua các thời kỳ:", indent=False, after=3)
code("""MATCH (p:Person)-[g:GIU_CHUC_VU]->(c:ChucVu)-[:THUOC_CO_QUAN]->(o:Organization)
WHERE o.name = 'Bộ Nội vụ'
RETURN c.name AS chuc_danh, 
       p.name AS ho_ten_lanh_dao, 
       g.start AS tu_ngay, 
       g.end AS den_ngay
ORDER BY g.start DESC;""")

para("Ví dụ truy vấn Cypher 3: Truy vấn các nội dung chỉ đạo điều hành của Thủ tướng Chính phủ đối với các bộ ngành:", indent=False, after=3)
code("""MATCH (p:Person {name: 'Phạm Minh Chính'})-[:ISSUED_BY]->(e:Event {event_type: 'CHI_DAO'})-[:TARGETS]->(o:Organization)
WHERE e.action_content IS NOT NULL
RETURN o.name AS co_quan_nhan_chi_dao,
       e.action_content AS noi_dung_chi_dao,
       e.deadline AS thoi_han_hoan_thanh,
       e.date AS ngay_chi_dao
ORDER BY e.date DESC
LIMIT 10;""")

# ================================================================== Tài liệu tham khảo
heading("Tài liệu tham khảo")
refs = [
    "[1] T.-N. Nguyen, B. T. Tran, T.-N. Luu, T. H. Nguyen, K.-H. Nguyen. *BKEE: Pioneering Event Extraction in the Vietnamese Language*. Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024), tr. 2421–2427, 2024.",
    "[2] D. Truong, D.-T. Vo, U. T. Nguyen. *Vietnamese Open Information Extraction*. In Proceedings of the 8th International Symposium on Information and Communication Technology (SoICT 2017), arXiv:1801.07804, 2017.",
    "[3] V. T. Mai và cộng sự. *Overview of VLSP RelEx shared task: A Data Challenge for Semantic Relation Extraction from Vietnamese News*. In Proceedings of the 7th International Workshop on Vietnamese Language and Speech Processing (VLSP 2020), tr. 92–98, 2020.",
    "[4] P. Christen. *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection*. Springer Science & Business Media, 2012.",
    "[5] A. Hogan và cộng sự. *Knowledge Graphs*. ACM Computing Surveys, 54(4), tr. 1–37, 2021.",
    "[6] Neo4j Graph Database và Graph Data Science Library (phần mềm). https://neo4j.com, 2026.",
    "[7] Underthesea – Vietnamese NLP Toolkit (phần mềm mã nguồn mở). https://github.com/undertheseanlp/underthesea, 2024.",
    "[8] A. Hagberg, D. Schult, P. Swart. *Exploring Network Structure, Dynamics, and Function using NetworkX*. In Proceedings of the 7th Python in Science Conference (SciPy 2008), tr. 11–15, 2008.",
]
for ref in refs:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.8)
    pf.first_line_indent = Cm(-0.8)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.15
    add_runs(p, ref, size=10.5)

doc.core_properties.title = "Báo cáo bài tập cuối kỳ – Đề tài 19"
doc.core_properties.author = "Nhóm thực hiện Đề tài 19"

doc.save(OUT1)
print(f"Đã lưu OUT1: {OUT1.relative_to(ROOT)}")
for out_path in [OUT2, ROOT / "report" / "Bao_Cao_De_Tai_19_1_CapNhat.docx", ROOT / "report" / "Bao_Cao_De_Tai_19_1_MoiNhat.docx", ROOT / "report" / "Bao_Cao_De_Tai_19_1_v3.docx"]:
    try:
        doc.save(out_path)
        print(f"Đã lưu bản cập nhật tại: {out_path.relative_to(ROOT)}")
        break
    except PermissionError:
        print(f"Tệp {out_path.name} đang mở trong Word, thử lưu tệp thay thế tiếp theo...")
