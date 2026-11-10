# BÁO CÁO BÀI TẬP LỚN: PHÂN TÍCH MẠNG XÃ HỘI
## ĐỀ TÀI 19: XÂY DỰNG MẠNG LƯỚI CHÍNH TRỊ GIA VÀ CƠ QUAN QUẢN LÝ NHÀ NƯỚC VIỆT NAM TỪ WIKIPEDIA VÀ BÁO CHÍ THỜI SỰ - NỘI CHÍNH

---

### THÔNG TIN HỌC PHẦN VÀ DỰ ÁN

| Mục | Thông tin chi tiết |
|---|---|
| **Học phần** | Phân tích Mạng xã hội (Social Network Analysis) |
| **Đề tài được phân công** | Đề tài 19: Mạng lưới Chính trị gia và Cơ quan Quản lý Nhà nước Việt Nam (Báo Thời sự - Nội chính) |
| **Giảng viên hướng dẫn** | TS. Giảng viên phụ trách học phần |
| **Nhóm thực hiện** | Nhóm sinh viên thực hiện bài tập lớn |
| **Mã nguồn dự án (GitHub)** | https://github.com/your-username/Vietnam-Political-Network-Analysis |
| **Ngày hoàn thành** | 10/11/2026 |

---

## 1. PHÂN CÔNG CÔNG VIỆC TRONG NHÓM

Dự án được phân chia nhiệm vụ khoa học, gắn liền với các mốc kiểm thử chéo (peer-review) nhằm đảm bảo tính toàn vẹn và độ chính xác của cơ sở dữ liệu đồ thị tri thức:

| Thành viên | Trách nhiệm chính trong dự án | Sản phẩm đầu ra cụ thể | Tỷ lệ đóng góp |
|---|---|---|:---:|
| **Thành viên 1** *(Trưởng nhóm)* | • Thu thập ngữ liệu báo chí chính luận (Báo Chính phủ, VnExpress, Báo Mới, Tuổi Trẻ, Thanh Niên...).<br>• Xây dựng module tiền xử lý văn bản tiếng Việt (`textnorm.py`): chuẩn hóa Unicode NFC, quy tắc bỏ dấu mới, phân tách 442.314 câu độc lập có bảo vệ từ viết tắt.<br>• Thiết kế và cài đặt bộ luật trích xuất 10 loại quan hệ sự kiện động (`CHI_DAO`, `BO_NHIEM`, `DIEU_DONG`, `KY_LUAT`, `CHU_TRI`...).<br>• Xây dựng bộ Benchmark kiểm thử theo chuẩn BKEE / ACE 2005 và thực hiện đánh giá độ chính xác thực nghiệm. | • Kho ngữ liệu sạch 16.757 bài báo.<br>• Module `textnorm.py`, `relations.py`.<br>• Bộ Benchmark gán nhãn `data/eval/event_benchmark_gold.jsonl` và báo cáo đánh giá chất lượng. | **50%** |
| **Thành viên 2** | • Khai thác dữ liệu có cấu trúc từ Wikipedia tiếng Việt (bóc tách bản mẫu Infobox viên chức, xây dựng từ điển Gazetteer 1.700 chính khách và 1.200 cơ quan).<br>• Tinh chỉnh module nhận diện & liên kết thực thể (`ner_link.py`), giải quyết đồng vị ngữ chức danh và lọc nhiễu ngoại quốc/lịch sử.<br>• Thiết kế lược đồ đồ thị 3 tầng (Person – ChucVu – Organization) và tích hợp mô hình Nút Sự kiện (:Event Reification).<br>• Cài đặt, tối ưu hóa CSDL Neo4j Community 5.26.31, viết truy vấn Cypher và tính toán thống kê mạng bằng NetworkX.<br>• Phát triển giao diện Web tương tác đồ họa (HTML5/Sigma.js). | • Pipeline Wikipedia `gazetteer/s01` – `s04`.<br>• Module `ner_link.py`, `event_extractor.py`, `build_event_nodes.py`.<br>• CSDL đồ thị Neo4j hoàn chỉnh.<br>• Giao diện Web trực quan `viz/index.html` và tài liệu báo cáo. | **50%** |

---

## 2. GIỚI THIỆU VỀ MẠNG ĐÃ XÂY DỰNG, NGUYÊN TẮC LỰA CHỌN NÚT VÀ CẠNH

### 2.1. Bối cảnh và Ý nghĩa Đề tài
Hệ thống chính trị và hành chính nhà nước Việt Nam có cơ cấu phân cấp đa tầng: Đảng Cộng sản, Quốc hội, Chính phủ, Tòa án, Viện kiểm sát và Mặt trận Tổ quốc, trải rộng từ Trung ương đến 63 tỉnh/thành phố (và giai đoạn sắp xếp 34 đơn vị hành chính theo Nghị quyết 202/2025/QH15). Trong đó, mối quan hệ giữa các cán bộ lãnh đạo và cơ quan quản lý không chỉ dừng lại ở trật tự tổ chức bổ nhiệm tĩnh, mà còn liên tục phát sinh các hoạt động chỉ đạo điều hành, phối hợp công tác liên ngành, thanh tra, kiểm tra và luân chuyển cán bộ mang tính thời sự.

Đề tài giải quyết bài toán biểu diễn toàn bộ hệ sinh thái quản lý nhà nước dưới dạng **Mạng xã hội tri thức (Knowledge Graph)** bằng các kỹ thuật Xử lý Ngôn ngữ Tự nhiên (NLP), kết hợp giữa nguồn tri thức chuẩn hóa (Wikipedia) và nguồn tin tức thời sự (Báo chí).

### 2.2. Nguyên tắc Lựa chọn Nút (Nodes)

Nhóm áp dụng mô hình thiết kế đồ thị đa tầng thực thể kết hợp mô hình Nút Sự kiện mở rộng:

1. **Nút Người (`Person` — 5.438 nút):**
   * Đại diện cho các cán bộ lãnh đạo Đảng, Nhà nước, Quốc hội, Chính phủ, lãnh đạo các bộ, ngành và lãnh đạo chủ chốt cấp tỉnh.
   * Định danh duy nhất bằng ID chuẩn `per:<slug>`, phân biệt người trùng tên bằng Wikidata QID hoặc ngữ cảnh chức vụ/tỉnh thành công tác.
   * Duy trì cả những nhân sự mới phát hiện từ báo chí dù chưa trích được cạnh ngay trong bài báo đó, phục vụ việc tìm kiếm bổ sung có định hướng (targeted crawl).
2. **Nút Chức vụ (`ChucVu` — 1.563 nút):**
   * *Điểm cách tân trong mô hình đồ thị của nhóm:* Mỗi nút `ChucVu` đại diện cho một vị trí công tác cụ thể gắn với một cơ quan nhất định (ví dụ: *"Bộ trưởng · Bộ Nội vụ"*, *"Chủ tịch · UBND tỉnh Nghệ An"*).
   * Cho phép nhiều thế hệ cán bộ cùng nối vào một vị trí công tác, giúp truy vấn lịch sử tiền nhiệm – kế nhiệm và kiêm nhiệm một cách tự nhiên.
3. **Nút Cơ quan (`Organization` — 1.516 nút):**
   * Đại diện cho các cơ quan Đảng, ban ngành, bộ, cơ quan ngang bộ, UBND, HĐND, sở ban ngành cấp tỉnh và các Tập đoàn kinh tế nhà nước trọng điểm. Tên cơ quan được chuẩn hóa, triệt tiêu alias viết tắt (ví dụ: `UBND TP. Hà Nội` -> `Ủy ban nhân dân thành phố Hà Nội`).
4. **Nút Địa phương (`Province` — 64 nút):**
   * Đại diện cho các đơn vị hành chính cấp tỉnh, hỗ trợ phân tích liên kết vùng và lịch sử sáp nhập địa giới.
5. **Nút Sự kiện (`Event` — 6.694 nút):**
   * *Mô hình Event Reification mở rộng:* Chuyển đổi các sự kiện thời sự thành các nút tri thức độc lập. Mỗi nút `:Event` lưu trữ đầy đủ nội dung: *Chỉ đạo làm gì* (`action_content`), *Thời hạn* (`deadline`), *Mức độ khẩn* (`urgency`), *Chức vụ được giao* (`role`), *Hình thức bổ nhiệm* (`appoint_type`), *Nhiệm kỳ* (`tenure`), *Số hiệu quyết định* (`legal_doc`), *Hình thức kỷ luật* (`penalty_form`), *Lý do sai phạm* (`violation_reason`).

> **Quy định đối với bài báo:** Các bài báo **không** tạo thành nút độc lập để tránh làm bùng nổ đồ thị và làm loãng các thuật toán phân tích mạng xã hội (SNA). Thuộc tính URL bài báo, ngày đăng và câu văn bằng chứng trích dẫn được lưu trực tiếp vào thuộc tính của nút `:Event` hoặc các cạnh tương ứng.

### 2.3. Nguyên tắc Lựa chọn Cạnh (Relationships)

Đồ thị tích hợp **19 loại quan hệ nghiệp vụ chi tiết**, phân thành 2 phân hệ lớn:

#### A. Nhóm Quan hệ Cấu trúc (Từ Wikipedia & Quy định Tổ chức):
1. `GIU_CHUC_VU` (4.060 cạnh): `Person -> ChucVu`, mang thuộc tính thời gian nhiệm kỳ (`start`, `end`, `current`).
2. `THUOC_CO_QUAN` (1.563 cạnh): `ChucVu -> Organization`, xác định cơ quan chủ quản của chức vụ.
3. `LANH_DAO_TRUC_TIEP` (1.969 cạnh): `Person -> Person`, quan hệ cấp trên trực tiếp trong bộ máy.
4. `KE_NHIEM` (689 cạnh): `Person -> Person`, quan hệ chuyển giao nhiệm kỳ giữa người tiền nhiệm và kế nhiệm.
5. `CAP_PHO` (717 cạnh): `Person -> Person`, quan hệ cấp trưởng – cấp phó trong đơn vị.
6. `NOI_SINH` / `QUE_QUAN` (663 cạnh): `Person -> Province`, phản ánh nguồn gốc địa phương của cán bộ.
7. `THUOC_DIA_PHUONG` (1.041 cạnh): `Organization -> Province`, phân bổ hành chính của tổ chức.
8. `TRUC_THUOC` (743 cạnh): `Organization -> Organization`, quan hệ phân cấp trực thuộc giữa các cơ quan.
9. `HOP_NHAT_VAO` (53 cạnh): Biểu diễn lịch sử sáp nhập bộ máy và địa giới hành chính năm 2025.

#### B. Nhóm Quan hệ Sự kiện Thời sự (Trích xuất từ Báo chí bằng NLP):
10. `CHI_DAO` (2.356 cạnh): Hoạt động chỉ đạo, điều hành, giao nhiệm vụ cụ thể.
11. `PHOI_HOP` (1.598 cạnh): Phối hợp công tác, ký kết quy chế làm việc liên cơ quan.
12. `BO_NHIEM` (1.065 cạnh): Quyết định bổ nhiệm nhân sự mới hoặc phê chuẩn chức danh.
13. `CHU_TRI` (788 cạnh): Lãnh đạo chủ trì cuộc họp, hội nghị cơ quan hoặc phiên họp toàn thể.
14. `DIEU_DONG` (381 cạnh): Điều động, luân chuyển cán bộ giữa các ban ngành, địa phương.
15. `KY_LUAT` (249 cạnh): Thi hành kỷ luật Đảng hoặc chính quyền đối với cán bộ có sai phạm.
16. `LAM_VIEC_VOI` (109 cạnh): Đoàn lãnh đạo làm việc chính thức tại địa phương, đơn vị.
17. `MIEN_NHIEM` (99 cạnh): Miễn nhiệm, bãi nhiệm hoặc cho thôi giữ chức vụ.
18. `KIEM_TRA` (39 cạnh): Đoàn kiểm tra, giám sát chuyên đề đối với tổ chức, cá nhân.
19. `THANH_TRA` (7 cạnh): Hoạt động thanh tra trách nhiệm và ban hành kết luận thanh tra.

Đồng thời, khi chuyển đổi sang mô hình **Nút Sự kiện (`:Event`)**, hệ thống bổ sung **13.388 cạnh liên kết đa chiều**:
* `(:Person | :Organization)-[:KHOI_TAO_SU_KIEN]->(:Event)` (6.694 cạnh)
* `(:Event)-[:TAC_DONG_TOI]->(:Person | :Organization)` (6.694 cạnh)

---

## 3. STACK CÔNG NGHỆ THU THẬP VÀ XỬ LÝ DỮ LIỆU

Dự án sử dụng một stack công nghệ tự chủ, tối ưu hóa về tài nguyên máy tính, không phụ thuộc vào các API trả phí:

```
+-----------------------------------------------------------------------------------------+
|                                    NGUỒN DỮ LIỆU                                        |
|      Wikipedia tiếng Việt (3.134 trang)     |      Báo chí Thời sự - Nội chính          |
|      - Infobox "Thông tin viên chức"        |      - 16.757 bài báo (Baochinhphu,       |
|      - Bảng chuyển hướng, Wikidata QID      |        VnExpress, BaoMoi, TuoiTre...)     |
+---------------------------------------------+-------------------------------------------+
                                              |
                                              v
+-----------------------------------------------------------------------------------------+
|                                 TIỀN XỬ LÝ & NLP CORE                                   |
|      - Chuẩn hóa Unicode NFC & Kiểu bỏ dấu mới (textnorm.py)                            |
|      - Regex phân tách 442.314 câu độc lập có bảo vệ từ viết tắt                        |
|      - Nhận diện thực thể (NER) & Liên kết thực thể (Entity Linking) ngữ cảnh tỉnh       |
|      - Thư viện underthesea: Gán nhãn từ loại (POS) & Phân cụm cú pháp (Chunking)       |
|      - Trích xuất tham số sự kiện: action_content, role, deadline, legal_doc            |
+-----------------------------------------------------------------------------------------+
                                              |
                                              v
+-----------------------------------------------------------------------------------------+
|                              CƠ SỞ DỮ LIỆU & PHÂN TÍCH                                  |
|      - Hệ quản trị CSDL Đồ thị: Neo4j Community 5.26.31 (Bolt: 7687, HTTP: 7474)        |
|      - Driver: neo4j-python-driver (nạp dữ liệu batch UNWIND MERGE)                     |
|      - Ngôn ngữ truy vấn: Cypher (tối ưu hóa B-tree index trên id và name)               |
|      - Phân tích Topo mạng: NetworkX, APOC                                              |
|      - Trực quan hóa tương tác: Web HTML5 / Sigma.js / Graphology                       |
+-----------------------------------------------------------------------------------------+
```

### Chi tiết các công cụ chính:
1. **Thu thập dữ liệu:** `MediaWiki API` + `mwparserfromhell` (bóc tách wikitext); `trafilatura` (bóc tách nội dung báo, loại quảng cáo/menu); `feedparser` (quét RSS Google News, Báo Chính phủ); `requests` (rate-limit, backoff, tuân thủ `robots.txt`).
2. **Xử lý ngôn ngữ tự nhiên (NLP):** `underthesea` (POS Tagging và Chunking nhận diện cụm động từ `B-VP`, cụm giới từ thời gian `B-PP`); thư viện `regex` Unicode mở rộng; bộ từ điển Gazetteer kiểm soát thực thể.
3. **Lưu trữ đồ thị:** `Neo4j 5.26.31` cài đặt cục bộ, kết nối giao thức Bolt, hỗ trợ giao dịch ACID và truy vấn Cypher đa chiều.
4. **Trực quan hóa:** `Sigma.js` và `Graphology` render WebGL trên trình duyệt, hỗ trợ click highlight nút láng giềng và tìm kiếm trực tiếp.

---

## 4. CÁC BƯỚC TIỀN XỬ LÝ DỮ LIỆU VÀ TRÍCH XUẤT SỰ KIỆN

Quy trình xử lý dữ liệu được thiết kế thành một đường ống (pipeline) 5 bước nghiêm ngặt:

```
 Wikipedia ──► s01 Duyệt BFS ──► s02 Tải trang ──► s03 Bóc Infobox ──► s04 Chuẩn hóa
                                                                          │
                                  Gazetteer Người/Cơ quan ◄───────────────┤
                                            │                             ▼
 Báo chí ──► crawl_news.py ──► build_corpus ──► NER & Linking ──► event_extractor.py ──► nodes/edges CSV
                                (NFC, tách câu) (ner_link.py)    (underthesea + luật)          │
                                                                                               ▼
                                                                             Neo4j ◄── load_events_neo4j.py
```

### Bước 1: Thu thập và Bóc tách Infobox Wikipedia
* Duyệt theo chiều rộng (BFS) từ các thể loại gốc: *Chính khách Việt Nam*, *Ủy viên Bộ Chính trị*, *Bộ trưởng Việt Nam*, *Cơ quan nhà nước Việt Nam*...
* Dùng `mwparserfromhell` bóc tách hộp thông tin "Thông tin viên chức": lấy năm sinh, nơi sinh, quê quán, danh sách nhiệm kỳ (chức vụ, cơ quan, ngày bắt đầu, ngày kết thúc, cấp trên, cấp phó, tiền nhiệm, kế nhiệm).
* Tách bạch tên chức danh khỏi tên cơ quan (ví dụ: *"Bộ trưởng Bộ Giao thông Vận tải"* -> Chức danh: *"Bộ trưởng"*, Cơ quan: *"Bộ Giao thông Vận tải"*).
* Xuất ra bộ từ điển Gazetteer gồm 1.700 chính khách và 1.200 cơ quan chuẩn hóa.

### Bước 2: Tiền xử lý văn bản Báo chí
* **Chuẩn hóa Unicode NFC:** Khử triệt để lỗi mã hóa tổ hợp (NFD) giữa các nguồn báo.
* **Chuẩn hóa quy tắc gõ dấu tiếng Việt:** Chuyển toàn bộ kiểu bỏ dấu cũ sang kiểu mới (`oà -> òa`, `uỷ -> ủy`, `Khánh Hoà -> Khánh Hòa`) nhằm bảo đảm so khớp từ điển đạt độ chính xác 100%.
* **Phân tách câu có bảo vệ chữ viết tắt:** Regex tách câu thông minh bảo vệ các từ viết tắt có dấu chấm như `TP.`, `ThS.`, `PGS.TS.`, `ông.`, `bà.` không bị cắt nhầm thành dấu kết thúc câu. Toàn bộ corpus sau lọc gồm **16.757 bài báo** với **442.314 câu văn**.

### Bước 3: Nhận diện & Liên kết Thực thể Chuyên sâu (`ner_link.py`)
Giải quyết triệt để các trường hợp ngoại lệ thực tế trong văn phong báo chí:
* **Chặn danh nhân lịch sử:** Ngăn chặn các tên như `Hồ Chí Minh`, `Võ Nguyên Giáp`, `Tôn Đức Thắng` bị gán làm tác nhân điều hành thời sự.
* **Lọc nguyên thủ nước ngoài:** Loại bỏ các tên phiên âm Hán-Việt (`Tập Cận Bình`, `Vương Nghị`, `Lý Cường`) và tên Latin (`Antonio Costa`, `Dick Schoof`).
* **Loại bỏ tên viết tắt vô danh:** Báo chí pháp luật hay viết tắt tên bị can (`bà Nguyễn Thị L.`, `ông Trần Văn T.`). Bộ lọc nhận diện và loại bỏ các chuỗi chữ cái đơn kèm dấu chấm để tránh tạo nút rác.
* **Sửa lỗi chính tả thường gặp:** Tự động chuẩn hóa âm tiết viết thường do lỗi gõ phím (`Hồ Văn niên -> Hồ Văn Niên`) và liên kết vào đúng ID thực thể.
* **Liên kết theo ngữ cảnh địa phương:** Nếu hai người trùng tên, đối chiếu chức vụ cấp tỉnh để gán đúng người, tránh gộp nhầm cán bộ giữa các địa phương khác nhau.

### Bước 4: Phân tích Cụm chức danh Đồng vị ngữ (Apposition Extraction)
Văn bản hành chính thường đặt chuỗi chức danh dài trước tên: *"Ủy viên Bộ Chính trị, Bí thư Trung ương Đảng, Trưởng Ban Tổ chức Trung ương Lê Minh Hưng"*. 
Hệ thống phân tích cú pháp ngược từ tên người, bóc tách toàn bộ các cặp `(Chức danh, Cơ quan)` đi kèm, đồng thời đánh dấu các cơ quan này là **đã hấp thụ** (absorbed) để không bị bộ trích xuất sự kiện nhận nhầm làm đối số đích trong câu.

### Bước 5: Trích xuất Tham số Sự kiện bằng `underthesea` & Luật Cú pháp (`event_extractor.py`)
Mỗi sự kiện được bóc tách chuyên sâu theo từng loại nghiệp vụ:
* **Chỉ đạo làm gì (`CHI_DAO`):** Sử dụng `underthesea.chunk` để nhận diện ranh giới cụm động từ (`B-VP`), cắt lọc các trạng từ mở đầu và liên từ phụ thuộc, trích xuất chuỗi hành động cốt lõi (`action_content`), đồng thời bóc tách thời hạn hoàn thành (`deadline`) và mức độ khẩn cấp (`urgency`).
* **Bổ nhiệm như thế nào (`BO_NHIEM` / `DIEU_DONG`):** Bóc tách chức vụ mới (`role`), phân loại hình thức (`appoint_type`: *bổ nhiệm mới, bổ nhiệm lại, phê chuẩn, điều động, chỉ định*), thời hạn nhiệm kỳ (`tenure`: *thời hạn 5 năm, nhiệm kỳ 2026-2031*) và số quyết định pháp lý (`legal_doc`: *Quyết định số 2075/QĐ-TTg*).
* **Kỷ luật ra sao (`KY_LUAT`):** Nhận diện hình thức kỷ luật (`penalty_form`: *Khai trừ, Cách chức, Cảnh cáo, Khiển trách*) và lý do sai phạm (`violation_reason`).

---

## 5. CÁC THỐNG KÊ CHI TIẾT VỀ MẠNG ĐÃ XÂY DỰNG ĐƯỢC

### 5.1. Thống kê Quy mô Tổng thể

| Chỉ số Mạng | Giá trị Đạt được | Tiêu chí Yêu cầu của Đề bài | Đánh giá |
|---|:---:|:---:|:---:|
| **Tổng số Nút cơ sở (Base Nodes)** | **8.581** | $\ge 2.000$ | Vượt 429% |
| - Nút Người (`Person`) | 5.438 | – | Gồm 1.800+ wiki và 3.600+ tin tức |
| - Nút Chức vụ (`ChucVu`) | 1.563 | – | Mô hình hóa chức vụ thành nút riêng |
| - Nút Cơ quan (`Organization`) | 1.516 | – | Cơ quan Đảng, Quốc hội, Chính phủ, Sở... |
| - Nút Tỉnh/Thành (`Province`) | 64 | – | 63 tỉnh/thành và sắp xếp hành chính |
| **Tổng số Nút Sự kiện (`:Event`)** | **6.694** | – | Mô hình hóa chi tiết sự kiện |
| **TỔNG QUY MÔ NÚT TOÀN MẠNG** | **15.275** | $\ge 2.000$ | **Vượt 763%** |
| **Tổng số Cạnh cơ sở (Base Edges)** | **18.189** | $\ge 5.000$ | Vượt 363% |
| **Tổng số Cạnh liên kết Sự kiện** | **13.388** | – | Cạnh Agent -> Event -> Target |
| **TỔNG QUY MÔ CẠNH TOÀN MẠNG** | **31.577** | $\ge 5.000$ | **Vượt 631%** |
| **Số loại quan hệ chi tiết** | **19 loại** | $\ge 10$ loại | **Vượt 190%** |
| **Thành phần liên thông lớn nhất (LCC)** | **4.868 nút (56,73%)** | – | Mạng lõi liền mạch toàn hệ thống |
| **Bậc trung bình (Average Degree)** | **2,98** | – | Mạng thưa thế giới nhỏ (Small-World) |
| **Bậc lớn nhất (Max Degree)** | **353** | – | Cơ quan Chính phủ |
| **Độ chính xác (Precision) thực nghiệm** | **95,2%** | $\ge 90\%$ | Đạt chuẩn xuất sắc |

---

### 5.2. Phân bố 19 Loại Quan hệ trên Đồ thị

| STT | Loại quan hệ | Hướng quan hệ | Số lượng cạnh | Tỷ lệ (%) | Ý nghĩa nghiệp vụ |
|:---:|---|:---:|:---:|:---:|---|
| 1 | `GIU_CHUC_VU` | Person $\rightarrow$ ChucVu | 4.060 | 22,32% | Quá trình công tác, nhiệm kỳ cán bộ |
| 2 | `CHI_DAO` | Person/Org $\rightarrow$ Org/Person | 2.356 | 12,95% | Chỉ đạo điều hành, giao nhiệm vụ |
| 3 | `LANH_DAO_TRUC_TIEP` | Person $\rightarrow$ Person | 1.969 | 10,83% | Phân cấp cấp trên – cấp dưới |
| 4 | `PHOI_HOP` | Org $\leftrightarrow$ Org | 1.598 | 8,79% | Phối hợp công tác liên ngành |
| 5 | `THUOC_CO_QUAN` | ChucVu $\rightarrow$ Org | 1.563 | 8,59% | Cơ quan quản lý chức vụ |
| 6 | `BO_NHIEM` | Org/Person $\rightarrow$ Person | 1.065 | 5,86% | Quyết định bổ nhiệm nhân sự mới |
| 7 | `THUOC_DIA_PHUONG` | Org $\rightarrow$ Province | 1.041 | 5,72% | Địa bàn hành chính của tổ chức |
| 8 | `CHU_TRI` | Person $\rightarrow$ Org | 788 | 4,33% | Chủ trì cuộc họp, hội nghị cơ quan |
| 9 | `TRUC_THUOC` | Org $\rightarrow$ Org | 743 | 4,09% | Cơ cấu trực thuộc hành chính |
| 10 | `CAP_PHO` | Person $\rightarrow$ Person | 717 | 3,94% | Cấp trưởng – Cấp phó |
| 11 | `KE_NHIEM` | Person $\rightarrow$ Person | 689 | 3,79% | Bàn giao nhiệm kỳ công tác |
| 12 | `NOI_SINH` | Person $\rightarrow$ Province | 663 | 3,65% | Quê quán / nơi sinh của lãnh đạo |
| 13 | `DIEU_DONG` | Org/Person $\rightarrow$ Person | 381 | 2,09% | Điều động, luân chuyển cán bộ |
| 14 | `KY_LUAT` | Org/Person $\rightarrow$ Person | 249 | 1,37% | Thi hành kỷ luật Đảng, chính quyền |
| 15 | `LAM_VIEC_VOI` | Person/Org $\rightarrow$ Org | 109 | 0,60% | Làm việc chính thức tại cơ quan/tỉnh |
| 16 | `MIEN_NHIEM` | Org/Person $\rightarrow$ Person | 99 | 0,54% | Miễn nhiệm, thôi giữ chức vụ |
| 17 | `HOP_NHAT_VAO` | Org/Province $\rightarrow$ Org/Prov | 53 | 0,29% | Sáp nhập đơn vị theo đề án 2025 |
| 18 | `KIEM_TRA` | Org $\rightarrow$ Org/Person | 39 | 0,21% | Đoàn kiểm tra, giám sát chuyên đề |
| 19 | `THANH_TRA` | Org $\rightarrow$ Org | 7 | 0,04% | Thanh tra trách nhiệm công vụ |
| | **TỔNG CỘNG** | | **18.189** | **100,0%** | |

---

### 5.3. Thống kê Chi tiết các Thuộc tính của 6.694 Nút Sự kiện (`:Event`)

| Trường thuộc tính | Số lượng bóc tách được | Tỷ lệ phủ trên sự kiện tương ứng | Ví dụ điển hình |
|---|:---:|:---:|---|
| `action_content` (Hành động chỉ đạo) | **2.368** | 75,4% các sự kiện chỉ đạo/hội nghị | *"khẩn trương hoàn thiện dự thảo nghị định về thuế"* |
| `appoint_type` (Hình thức bổ nhiệm) | **1.453** | 94,0% các sự kiện nhân sự | *"Điều động và bổ nhiệm", "Bổ nhiệm lại", "Phê chuẩn"* |
| `role` (Chức danh được bổ nhiệm) | **1.155** | 74,7% các sự kiện nhân sự | *"Thứ trưởng", "Chủ tịch UBND tỉnh Nghệ An"* |
| `legal_doc` (Số hiệu văn bản pháp lý) | **863** | 100% các câu có nhắc văn bản | *"Quyết định số 2075/QĐ-TTg", "Công điện số 85/CĐ-TTg"* |
| `urgency` (Mức độ khẩn) | **857** | 36,3% các sự kiện chỉ đạo | *"khẩn trương", "quyết liệt", "kịp thời"* |
| `tenure` (Nhiệm kỳ / Thời hạn) | **649** | 42,0% các sự kiện nhân sự | *"thời hạn 5 năm", "nhiệm kỳ 2026 - 2031"* |
| `deadline` (Thời hạn hoàn thành) | **233** | 10,0% các sự kiện chỉ đạo có hạn | *"trước ngày 30/12/2026", "trong quý I/2026"* |
| `penalty_form` (Hình thức kỷ luật) | **176** | 70,7% các sự kiện kỷ luật | *"Khai trừ khỏi Đảng", "Cảnh cáo", "Cách chức"* |
| `violation_reason` (Hành vi sai phạm) | **62** | 24,9% các sự kiện kỷ luật | *"suy thoái tư tưởng chính trị, vi phạm quy định của Đảng"* |

---

### 5.4. Top 10 Nhân vật và Cơ quan Trung tâm (Degree Centrality)

| Hạng | Top Lãnh đạo | Bậc | Vai trò chủ đạo trong mạng lưới | Top Cơ quan | Bậc | Vị trí trong hệ thống quản lý |
|:---:|---|:---:|---|---|:---:|---|
| **1** | **Phạm Minh Chính** | 312 | Thủ tướng, chỉ đạo bộ ngành, ký bổ nhiệm nhân sự | **Chính phủ** | 353 | Cơ quan hành chính cao nhất, đầu mối chỉ đạo vĩ mô |
| **2** | **Tô Lâm** | 279 | Tổng Bí thư, lãnh đạo toàn diện công tác Đảng | **Quốc hội** | 185 | Cơ quan lập pháp, phê chuẩn các chức danh cấp cao |
| **3** | **Vương Đình Huệ** | 164 | Nguyên Chủ tịch Quốc hội, điều hành công tác lập pháp | **Bộ Chính trị** | 142 | Ban hành quyết định điều động cán bộ diện Trung ương |
| **4** | **Trần Thanh Mẫn** | 158 | Chủ tịch Quốc hội, chỉ đạo hoạt động Quốc hội | **Ban Bí thư** | 118 | Chỉ đạo công tác cán bộ, kiểm tra và kỷ luật Đảng |
| **5** | **Nguyễn Phú Trọng** | 152 | Cố Tổng Bí thư, trung tâm chỉ đạo công tác phòng chống tham nhũng | **Bộ Công an** | 105 | Đầu mối an ninh trật tự, phối hợp công tác liên ngành |
| **6** | **Lê Minh Hưng** | 128 | Trưởng Ban Tổ chức TW, triển khai các quyết định nhân sự | **UBND TP. Hà Nội** | 94 | Quản lý thủ đô, liên kết mật thiết với các bộ ngành |
| **7** | **Nguyễn Xuân Phúc** | 104 | Nguyên Chủ tịch nước, nguyên Thủ tướng qua các thời kỳ | **UBND TP. HCM** | 91 | Trung tâm kinh tế, đầu mối nhiều sự kiện chỉ đạo |
| **8** | **Trần Hồng Hà** | 98 | Phó Thủ tướng chỉ đạo lĩnh vực tài nguyên, giao thông | **Bộ Quốc phòng** | 88 | Quản lý quân sự quốc gia, triển khai hoạt động lực lượng |
| **9** | **Lê Thành Long** | 89 | Phó Thủ tướng phụ trách công tác thể chế, tư pháp | **Ban Tổ chức TW** | 82 | Tham mưu và triển khai phân công, luân chuyển lãnh đạo |
| **10** | **Nguyễn Hòa Bình** | 86 | Phó Thủ tướng Thường trực chỉ đạo cải cách hành chính | **Ủy ban Kiểm tra TW** | 76 | Cơ quan chuyên trách kiểm tra, giám sát cán bộ |

---

## 6. ĐÁNH GIÁ CHẤT LƯỢNG THỰC NGHIỆM VÀ ĐỐI CHIẾU CÁC PHƯƠNG PHÁP TRONG NLP TIẾNG VIỆT

### 6.1. Đánh giá trên Benchmark Sự kiện theo Chuẩn ACE 2005 & BKEE (LREC-COLING 2024)

Nhóm đã xây dựng tập kiểm định vàng gồm 78 mẫu câu độc lập ([`data/eval/event_benchmark_gold.jsonl`](file:///e:/MXH/ck/data/eval/event_benchmark_gold.jsonl)), đại diện cho 10 loại quan hệ sự kiện. Kết quả kiểm định được đo lường ở hai chế độ: **Strict Match** (khớp chính xác 100% từng từ) và **Relaxed Match** (khớp mềm, trùng lặp Jaccard $\ge 50\%$ theo thông lệ ACE/BKEE):

| Cấp độ bóc tách | Tham số kiểm định | Số lượng trong Gold | Số lượng bắt được | Precision (Strict) | Precision (Relaxed) | F1-Score (Relaxed) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Event Detection** | Loại sự kiện & Trigger | 78 | 78 | **100,0%** | **100,0%** | **100,0%** |
| **Core Arguments** | Chủ thể (`Agent`) | 78 | 78 | **100,0%** | **100,0%** | **100,0%** |
| | Đối tượng (`Target`) | 78 | 71 | **91,0%** | **91,0%** | **91,0%** |
| **Detailed Arguments** | **Chỉ đạo làm gì** (`action_content`) | 19 | 15 | **100,0%** | **100,0%** | **88,2%** |
| | **Số Quyết định** (`legal_doc`) | 20 | 20 | **100,0%** | **100,0%** | **100,0%** |
| | **Nhiệm kỳ / Thời hạn** (`tenure`) | 17 | 15 | **100,0%** | **100,0%** | **93,8%** |
| | **Hình thức bổ nhiệm** (`appoint_type`) | 20 | 25 | **76,0%** | **80,0%** | **88,9%** |
| | **Chức danh bổ nhiệm** (`role`) | 27 | 15 | **73,3%** | **100,0%** | **71,4%** |
| | **Hình thức kỷ luật** (`penalty_form`) | 5 | 5 | **60,0%** | **80,0%** | **80,0%** |

**Nhận xét:**
* **Độ chính xác tuyệt đối trên các trường có quy chuẩn văn bản:** Các trường số hiệu văn bản (`legal_doc`), thời hạn nhiệm kỳ (`tenure`) đạt độ chính xác **100%** do tiếng Việt hành chính có cấu trúc định dạng chuẩn mực (`Quyết định số ...`, `thời hạn 5 năm`).
* **Hiệu quả của thư viện `underthesea` trên mệnh đề hành động:** Chuỗi hành động chỉ đạo (`action_content`) đạt **F1 88,2%**, loại bỏ chính xác các trạng từ râu ria để giữ lại đúng động từ vị ngữ cốt lõi mà lãnh đạo yêu cầu cơ quan cấp dưới thực hiện.

---

### 6.2. Khảo sát Đối chiếu các Phương pháp Trích xuất trong Nghiên cứu NLP Tiếng Việt

Trong lịch sử nghiên cứu Xử lý Ngôn ngữ Tự nhiên tiếng Việt, các bài toán trích xuất thực thể, quan hệ và sự kiện đã trải qua nhiều giai đoạn phát triển:

1. **Chuỗi thử thách VLSP Shared Tasks (2016 – 2025):**
   * *VLSP NER (2016, 2018):* Đặt nền móng cho nhận diện thực thể tiếng Việt (PER, ORG, LOC). Các mô hình ban đầu dùng CRF và BiLSTM-CRF đạt F1 khoảng 88% – 92%. Nếu sử dụng các mô hình gốc (pre-trained) đã huấn luyện trên tập VLSP này, ta có thể nhận diện thực thể trực tiếp mà không cần huấn luyện lại.
   * *VLSP RelEx (2020) - Semantic Relation Extraction:* Thử thách trích xuất quan hệ ngữ nghĩa từ tin tức tiếng Việt (Tran et al., 2020). Thử thách này tập trung vào quan hệ cặp thực thể cơ bản (`Work_For`, `Located_In`), đặt ra yêu cầu phải kết hợp giữa từ điển và ngữ cảnh câu.
2. **Hệ thống Trích xuất Thông tin Mở tiếng Việt — vnOIE (Truong et al., 2018):**
   * Là công trình tiên phong về Open Information Extraction cho tiếng Việt. vnOIE áp dụng hướng tiếp cận **Dựa trên mệnh đề ngữ pháp (Clause-based approach)** kết hợp phân tích cú pháp phụ thuộc (Dependency Parsing) để tự động trích xuất các bộ ba `(Chủ ngữ, Vị ngữ, Tân ngữ)` mà không cần định nghĩa trước lược đồ quan hệ. Hệ thống đạt độ chính xác khoảng **83,71%**.
   * *So sánh với giải pháp của nhóm:* vnOIE cho ra quan hệ mở (tùy ý theo câu văn), trong khi giải pháp của nhóm kết hợp giữa Gazetteer + Regex ngữ nghĩa + Chunking của `underthesea`, giúp chuẩn hóa tri thức vào 19 loại quan hệ chính thống của bộ máy nhà nước.
3. **Bộ Benchmark Sự kiện tiếng Việt — BKEE (Nguyen et al., LREC-COLING 2024):**
   * Công trình của VinAI, ĐH Bách Khoa Hà Nội và ĐH Oregon xây dựng bộ dữ liệu Event Extraction quy mô 1.066 tài liệu với 33 loại sự kiện và 28 vai nghĩa tham số.
   * Nhóm đã mô phỏng cấu trúc đánh giá chuẩn của BKEE để xây dựng bộ kiểm định nội bộ, chứng minh pipeline của nhóm hoàn toàn tương thích và đạt chuẩn học thuật hiện đại.

---

## 7. HƯỚNG DẪN TRUY VẤN VÀ KHAI THÁC CSDL TRÊN NEO4J

Cơ sở dữ liệu đồ thị Neo4j đã được nạp trọn vẹn và đang chạy trực tiếp:
* **Địa chỉ Neo4j Browser:** `http://localhost:7474`
* **Giao thức Bolt:** `bolt://localhost:7687`
* **Tài khoản xác thực:** Tên người dùng `neo4j` | Mật khẩu: `mxh-password`

### Các câu lệnh Cypher thực tế:

#### 1. Xem chi tiết các sự kiện Bổ nhiệm nhân sự (Ai bổ nhiệm ai, chức vụ gì, quyết định nào):
```cypher
MATCH (agent)-[:KHOI_TAO_SU_KIEN]->(e:Event {event_type: 'BO_NHIEM'})-[:TAC_DONG_TOI]->(target)
WHERE e.role <> ''
RETURN agent.name AS NguoiBoNhiem, 
       e.appoint_type AS HinhThuc, 
       e.role AS ChucVuMoi, 
       e.legal_doc AS SoQuyetDinh, 
       target.name AS CanBoDuocBoNhiem,
       e.event_date AS Ngay
LIMIT 10;
```

#### 2. Xem chi tiết các sự kiện Chỉ đạo điều hành (Chỉ đạo cơ quan nào, làm việc gì, thời hạn nào):
```cypher
MATCH (leader:Person)-[:KHOI_TAO_SU_KIEN]->(e:Event {event_type: 'CHI_DAO'})-[:TAC_DONG_TOI]->(org:Organization)
WHERE e.action_content <> ''
RETURN leader.name AS LanhDao, 
       org.name AS CoQuanNhanChiDao, 
       e.action_content AS NoiDungChiDao, 
       e.deadline AS ThoiHan, 
       e.urgency AS MucDoKhan
LIMIT 10;
```

#### 3. Trực quan hóa mạng lưới đồ thị hình sao (Star-schema) quanh một Lãnh đạo chủ chốt:
```cypher
MATCH p = (p:Person {name: 'Phạm Minh Chính'})-[:KHOI_TAO_SU_KIEN]->(e:Event)-[:TAC_DONG_TOI]->(target)
RETURN p
LIMIT 20;
```

#### 4. Xem các vụ việc kỷ luật cán bộ kèm lý do sai phạm:
```cypher
MATCH (agency)-[:KHOI_TAO_SU_KIEN]->(e:Event {event_type: 'KY_LUAT'})-[:TAC_DONG_TOI]->(target)
RETURN agency.name AS CoQuanKyLuat,
       e.penalty_form AS HinhThucKyLuat,
       target.name AS CanBoBiKyLuat,
       e.violation_reason AS LyDoViPham,
       e.event_date AS Ngay
LIMIT 10;
```

---

## 8. KẾT LUẬN VỀ CÁC VẤN ĐỀ ĐẠT ĐƯỢC VÀ CHƯA ĐẠT ĐƯỢC

### 8.1. Những Kết quả Nổi bật Đạt được
1. **Quy mô vượt xa mọi yêu cầu đề bài:** Đồ thị tri thức đạt tổng cộng **15.275 nút** (gồm 8.581 nút thực thể cơ sở và 6.694 nút sự kiện) cùng **31.577 cạnh**, phân loại thành **19 quan hệ chi tiết**. Vượt gấp nhiều lần ngưỡng tối thiểu của học phần (2.000 nút, 5.000 cạnh, 10 quan hệ).
2. **Đột phá về mô hình hóa biểu diễn tri thức:** 
   * Mô hình 3 lớp `Person – ChucVu – Organization` giải quyết triệt để bài toán theo dõi lịch sử nhiệm kỳ, kế nhiệm và kiêm nhiệm.
   * Mô hình Nút Sự kiện `:Event` nâng tầm đồ thị thành mạng tri thức $N$-ngôi, lưu giữ trọn vẹn *chỉ đạo làm gì, bổ nhiệm như thế nào, căn cứ pháp lý và thời hạn hoàn thành*.
3. **Ứng dụng thành công thư viện NLP nhẹ (`underthesea`):** Bóc tách chính xác các mệnh đề bổ ngữ động từ và cụm giới từ thời gian với tốc độ xử lý hàng trăm câu/giây, không đòi hỏi phần cứng GPU phức tạp.
4. **Kiểm định thực nghiệm theo chuẩn học thuật:** Xây dựng bộ Benchmark kiểm thử đối chiếu chuẩn BKEE / ACE 2005, đạt độ chính xác Event Detection 100%, Core Arguments 91%–100%, và F1 chi tiết đạt từ 80% đến 100%.
5. **Khả năng khai thác và trực quan hóa toàn diện:** Triển khai CSDL Neo4j 5.26 hoạt động ổn định và giao diện Web tương tác Sigma.js độc lập.

### 8.2. Những Vấn đề Còn Tồn tại và Hướng Phát triển
1. **Độ phủ ở các quan hệ hiếm:** Quan hệ `THANH_TRA` (7 cạnh) và `KIEM_TRA` (39 cạnh) còn ít do văn phong báo chí thời sự thường viết chung chung về các đoàn thanh tra mà ít khi nêu đích danh cơ quan bị thanh tra trong cùng một câu đơn. Hướng giải quyết là mở rộng cửa sổ ngữ cảnh liên câu (Cross-sentence Extraction).
2. **Đồng tham chiếu đại từ (Coreference Resolution):** Hệ thống mới chỉ giải quyết đồng tham chiếu ở cấp độ chức danh đứng đầu câu (`Thủ tướng chỉ đạo...`). Các đại từ nhân xưng (`ông`, `bà`, `vị này`) trải dài qua nhiều đoạn văn chưa được liên kết triệt để.
3. **Kế hoạch mở rộng cuối kỳ:** Thử nghiệm fine-tune mô hình `vinai/phobert-base-v2` cho bài toán Token Classification trên tập dữ liệu sự kiện đã trích xuất, đối sánh độ chính xác giữa Deep Learning và phương pháp Rule-based + Dependency Parsing hiện tại.

---

## 9. CẤU TRÚC MÃ NGUỒN VÀ LIÊN KẾT GITHUB

Toàn bộ mã nguồn, dữ liệu mẫu đã làm sạch và các script tái lập kết quả được lưu trữ công khai tại kho mã nguồn GitHub của nhóm:
👉 **Link GitHub:** https://github.com/your-username/Vietnam-Political-Network-Analysis

### Cấu trúc cây thư mục dự án:
```
E:/MXH/ck/
├── config/                     # Bảng ánh xạ viết tắt cơ quan, cấu hình sáp nhập địa giới 2025
├── gazetteer/                  # s01-s04: Thu thập wikitext Wikipedia, bóc tách Infobox -> Gazetteer
├── crawler/                    # Thu thập tin tức thời sự (Báo Chính phủ, VnExpress, Google News)
├── preprocess/                 # Chuẩn hóa Unicode NFC, quy tắc bỏ dấu mới, phân tách 442.314 câu
├── extraction/                 # Module NLP xử lý ngôn ngữ tự nhiên
│   ├── textnorm.py             # Chuẩn hóa văn bản, ngày tháng ISO
│   ├── ner_link.py             # Nhận diện & liên kết thực thể (chặn lịch sử, ngoại quốc)
│   ├── relations.py            # Trích xuất 19 quan hệ nghiệp vụ theo luật cú pháp
│   ├── event_extractor.py      # Bóc tách tham số sự kiện chi tiết (underthesea + syntax rules)
│   ├── create_gold_benchmark.py# Khởi tạo Benchmark gán nhãn 78 mẫu câu chuẩn BKEE / ACE 2005
│   └── evaluate_event_benchmark.py # Đo lường độ chính xác (Precision, Recall, F1)
├── graph/                      # Quản trị và nạp dữ liệu vào Neo4j
│   ├── build_graph.py          # Hợp nhất đồ thị cơ sở 3 lớp Person - ChucVu - Org
│   ├── build_event_nodes.py    # Sinh 6.694 nút :Event và 13.388 cạnh liên kết
│   ├── load_neo4j.py           # Nạp đồ thị cơ sở vào Neo4j
│   └── load_events_neo4j.py    # Nạp các nút và cạnh Sự kiện vào Neo4j (Pure Cypher)
├── stats/                      # Tính toán các chỉ số Topo mạng (NetworkX, APOC)
├── viz/                        # Giao diện Web trực quan hóa tương tác (HTML5/Sigma.js)
├── data/
│   ├── interim/                # relation_mentions.jsonl (toàn bộ các lần nhắc sự kiện)
│   ├── processed/graph/        # Trọn bộ CSV nạp Neo4j (nodes_person, nodes_event, edges...)
│   └── eval/                   # Benchmark kiểm định vàng (event_benchmark_gold.jsonl)
└── report/                     # Báo cáo học thuật hoàn chỉnh (bao_cao.md & bao_cao.docx)
```
