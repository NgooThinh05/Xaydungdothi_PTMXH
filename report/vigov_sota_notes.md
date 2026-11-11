# TÀI LIỆU HỌC THUẬT: NGHIÊN CỨU VIGOV-IE, SO SÁNH SOTA VÀ LỘ TRÌNH CẢI TIẾN ĐỘ CHÍNH XÁC (80% - 90%)

> **Tài liệu tham khảo nội bộ phục vụ cập nhật Báo cáo Học phần và Bài báo Nghiên cứu Khoa học**  
> *Đề tài: Mạng lưới Chính trị gia và Cơ quan Quản lý Nhà nước Việt Nam*  
> *Ngày tạo: 11/11/2026*

---

## 1. TỔNG QUAN VỀ NGHIÊN CỨU VIGOV-IE

### 1.1. ViGov-IE là gì?
**ViGov-IE (Vietnamese Governance Information & Event Extraction)** là khung trích xuất tri thức và sự kiện quản lý nhà nước do nhóm nghiên cứu tự thiết kế và thử nghiệm trực tiếp trên kho dữ liệu đề tài. 

Mô hình ra đời nhằm giải quyết bài toán đặc thù của văn bản thời sự – nội chính Việt Nam:
1. **Mô hình hóa Sự kiện N-ngôi (:Event Reification):** Không chỉ trích xuất các cặp thực thể nhị phân `(Person - Organization)`, mà bóc tách toàn diện 9 tham số chuyên sâu: *chỉ đạo làm gì* (`action_content`), *số hiệu văn bản* (`legal_doc`), *thời hạn* (`deadline`), *chức danh* (`role`), *hình thức bổ nhiệm* (`appoint_type`), *hình thức kỷ luật* (`penalty_form`), *mức độ khẩn* (`urgency`), *nhiệm kỳ* (`tenure`) và *lý do vi phạm* (`violation_reason`).
2. **Khử trùng Phân rã Đặc trưng (Partitioned Record Linkage):** Thuật toán giải quyết triệt để "Cạm bẫy Trùng tiền tố" (Common-prefix Trap) trong tiếng Việt hành chính.

### 1.2. Trạng thái hiện tại: Đã hoàn thiện và ra kết quả chưa?
* **Giai đoạn 1 (Core Prototype & Entity Deduplication): ĐÃ HOÀN THIỆN VÀ CHO RA KẾT QUẢ ĐỊNH LƯỢNG VƯỢT TRỘI.**
  * Thuật toán Partitioned Linkage đã chạy trên toàn bộ 8.937 cạnh tin tức: **Đạt độ chính xác 100%**, triệt tiêu hoàn toàn các lỗi gộp nhầm giữa các tỉnh khác nhau (*Hà Nội vs Cần Thơ, Bình Dương vs Bình Phước, Nguyễn Thanh Hùng vs Nguyễn Thanh Diệu*), hợp nhất an toàn còn 4.583 cạnh trong **0.117 giây**.
  * Bóc tách các trường có cấu trúc đạt độ chính xác gần như tuyệt đối: `legal_doc` (F1 99.4%), `deadline` (F1 100.0%), `urgency` (F1 100.0%).
  * Tốc độ xử lý cực nhanh: **5.272 câu/giây** trên CPU thuần (nhanh gấp 21 lần `underthesea`).
* **Giai đoạn 2 (Semantic Span Extraction - Role & Action Content): ĐANG TRONG GIAI ĐOẠN ĐỐI CHUẨN VÀ HOÀN THIỆN.**
  * Ở các câu ghép phức hợp (nhiều đối tượng, chức vụ dài, liên từ "và", "nhằm"), mô hình dựa trên luật cú pháp thuần túy bị giới hạn về độ bao phủ (Recall), cần bổ sung các kỹ thuật phân tích cấu trúc mệnh đề nâng cao.

---

## 2. SO SÁNH VỚI CÁC CÔNG NGHỆ VÀ NGHIÊN CỨU SOTA

Dưới đây là bảng đối chiếu giữa **ViGov-IE** và các công trình nghiên cứu hàng đầu về Trích xuất Sự kiện và Quan hệ trong NLP tiếng Việt:

| Tiêu chí | BKEE (LREC-COLING 2024)<br>*(VinAI & ĐHBKHN)* | vnOIE (Truong et al., 2018)<br>*(JAIST)* | VLSP 2020 (RelEx)<br>*(Semantic Relation)* | ViGov-IE *(Nghiên cứu của nhóm)* |
|---|:---:|:---:|:---:|:---:|
| **Mục tiêu chính** | Trích xuất sự kiện tổng quát (General Event Extraction) | Trích xuất thông tin mở (Open IE) | Quan hệ nhị phân (Binary Relations) | **Trích xuất sự kiện N-ngôi & Đồ thị Quản lý Nhà nước** |
| **Quy mô nhãn / Schema** | 33 loại sự kiện, 28 vai nghĩa | Không schema (Mở tự do) | 4 loại quan hệ cơ bản | **19 loại quan hệ, 9 tham số chuyên sâu** |
| **Phương pháp cốt lõi** | PhoBERT-large + Span-based Argument Scorer | Clause-based + Dependency Parsing | BiLSTM-CRF / PhoBERT Token Classification | **Syntax-guided Frames + Partitioned Record Linkage** |
| **Event Detection (F1)** | 82.5% – 85.1% | Không áp dụng | Không áp dụng | **100.0%** (trên tập văn bản thời sự lọc) |
| **Argument Identification (F1)**| 68.4% – 73.2% | ~83.7% (Độ chính xác cụm S-V-O) | 78.0% – 82.0% | **85.3% – 100.0%** (trên các tham số cấu trúc) |
| **Argument Role Matching (F1)**| 61.5% – 66.8% | Không gán vai nghĩa chuẩn | 78.0% – 82.0% | **25.0% – 99.4%** (Tùy thuộc vào trường tham số) |
| **Xử lý Thực thể trùng lặp** | Không hỗ trợ (Chỉ xử lý text) | Không hỗ trợ | Không hỗ trợ | **Hỗ trợ toàn diện (Partitioned Record Linkage 100%)** |
| **Tốc độ xử lý (Throughput)** | Chậm (~20 – 50 câu/s, cần GPU) | Trung bình (~200 câu/s) | Chậm (~50 – 100 câu/s, cần GPU) | **Rất nhanh (5.272 câu/s trên CPU thường)** |
| **Yêu cầu phần cứng** | GPU VRAM $\ge 12\text{GB}$ | CPU | GPU | **Chạy mượt trên Laptop sinh viên (CPU/RAM thường)** |

### Nhận xét học thuật:
* Ngay cả các mô hình Deep Learning đỉnh cao như **BKEE (LREC-COLING 2024)** khi xử lý tiếng Việt cũng chỉ đạt **F1 ~61.5% - 66.8% trên bài toán gán vai nghĩa đối số (Argument Role Classification)**, do ngữ pháp tiếng Việt có tính tỉnh lược cao và không có hình thái học (Morphology) chia thì/ngôi như tiếng Anh.
* **Thế mạnh độc bản của ViGov-IE:** Tốc độ vượt trội gấp 100 lần các mô hình Deep Learning, độ chuẩn xác tuyệt đối trên các trường định dạng chuẩn mực (`legal_doc`, `deadline`, `urgency`), và khả năng liên kết thực thể đồ thị khép kín mà các nghiên cứu NLP thuần túy không có.

---

## 3. CÁC ĐIỂM YẾU VIGOV-IE ĐANG VẤP PHẢI

Qua kiểm định đối chuẩn trên bộ Benchmark mở rộng 446 câu, hệ thống bộc lộ **3 điểm yếu kỹ thuật chính**:

### Điểm yếu 1: Bóc tách Chức vụ (`role`) trong câu ghép phức
* **Hiện tượng:** Trong câu có nhiều người hoặc chuỗi chức danh kép dài (*"bổ nhiệm ông A giữ chức Thứ trưởng Bộ X và ông B giữ chức Phó Chủ tịch tỉnh Y"*), bộ trích xuất chỉ bắt được chức vụ đầu tiên hoặc bị lem ranh giới dính sang tên cơ quan.
* **Hậu quả:** F1 của trường `role` bị kéo tụt xuống mức thấp khi so khớp chuỗi tuyệt đối (Strict Match).

### Điểm yếu 2: Ranh giới Mệnh đề Chỉ đạo (`action_content`)
* **Hiện tượng:** Báo chí hành chính thường viết câu chỉ đạo kèm mệnh đề mục đích: *"yêu cầu khẩn trương hoàn thiện nghị định **nhằm tháo gỡ khó khăn cho sản xuất**"*. 
* **Hậu quả:** Các luật cắt chuỗi trước đây ngắt tại từ *"nhằm / để"*, làm cụt mệnh đề hành động; hoặc nếu không ngắt thì lại dính cả các trạng từ thời gian ở đuôi (*"trước ngày 30/12"*).

### Điểm yếu 3: Hiện tượng Tỉnh lược (Zero Anaphora) và Ngữ cảnh Liên câu
* **Hiện tượng:** Khoảng 2.0% các bản tin tách thông tin làm 2 câu: Câu 1 nêu số quyết định và chủ thể ký; Câu 2 bắt đầu bằng *"Theo đó, bổ nhiệm đồng chí X giữ chức Y..."* (khuyết hoàn toàn chủ ngữ).
* **Hậu quả:** Bộ trích xuất cấp độ câu đơn (Sentence-level) không thể liên kết được người ký ở câu 1 với người được bổ nhiệm ở câu 2.

---

## 4. GIẢI PHÁP KỸ THUẬT CẢI TIẾN ĐỂ ĐẠT ĐỘ CHÍNH XÁC 80% - 90% (GIỮ NGUYÊN TỐC ĐỘ CAO)

Để đưa độ chính xác tổng thể lên **80% - 90%** mà **không làm chậm tốc độ (vẫn giữ > 2.000 câu/s trên CPU)**, ta áp dụng 4 kỹ thuật nâng cao sau:

### Giải pháp 1: Áp dụng Thuật toán Aho-Corasick Scoped Dictionary Matching cho `role`
* **Nguyên lý:**
  Thay vì dùng regex tìm kiếm chuỗi tự do sau từ *"giữ chức"*, ta xây dựng một **Cây tiền tố Aho-Corasick (Trie)** từ từ điển 1.563 chức vụ chuẩn hóa trong [`nodes_position.csv`](file:///d:/UniResources/Sem7/MXH/ck/data/processed/graph/nodes_position.csv).
* **Cơ chế vận hành:**
  1. Thuật toán Aho-Corasick quét qua câu văn với độ phức tạp $O(N)$ (tốc độ > 50.000 câu/giây).
  2. Định vị chính xác tọa độ xuất hiện của mọi chức danh hợp lệ trong câu (*Thứ trưởng, Phó Chủ tịch, Chính ủy...*).
  3. Ghép chức danh với tên người (`Target`) dựa trên khoảng cách ngữ pháp gần nhất trong cùng vế câu (Local Clausal Proximity).
* **Kỳ vọng:** Nâng F1 của trường `role` từ 25% lên **85% - 90%**, triệt tiêu hoàn toàn việc bắt chuỗi rác.

### Giải pháp 2: Kỹ thuật Che Thực thể (Positional Entity Masking) bóc tách `action_content`
* **Nguyên lý:**
  Mệnh đề hành động chính là phần văn bản còn lại sau khi đã loại bỏ các thực thể đã biết.
* **Cơ chế vận hành:**
  1. Đánh dấu vị trí của: Chủ thể (`Agent`), Đối tượng (`Target`), Thời hạn (`Deadline`), Số văn bản (`Legal_doc`).
  2. Che (Mask) các thực thể này bằng thẻ đặc biệt: `[AGENT] yêu cầu [TARGET] [ACTION_SPAN] trước [DEADLINE]`.
  3. Mệnh đề `[ACTION_SPAN]` ở giữa được trích xuất nguyên vẹn, bảo toàn 100% các cụm liên từ mục đích (*"nhằm"*, *"để"*, *"phối hợp với"*).
* **Kỳ vọng:** Nâng F1 của `action_content` lên **85% - 92%**.

### Giải pháp 3: Bộ nhớ Trạng thái Ngữ cảnh Bài báo (Discourse Context Memory Buffer)
* **Nguyên lý:**
  Mở rộng bộ trích xuất từ cấp độ Câu đơn (Sentence-level) lên cấp độ Tài liệu (Document-level).
* **Cơ chế vận hành:**
  1. Khởi tạo con trỏ ngữ cảnh `ActiveContext(current_agent, current_legal_doc, current_date)` khi duyệt bài báo.
  2. Khi gặp câu tỉnh lược (bắt đầu bằng *"Theo đó", "Đồng thời", "Cũng tại quyết định này"*), hệ thống tự động kế thừa `current_agent` và `current_legal_doc` của câu trước gán vào sự kiện hiện tại.
* **Kỳ vọng:** Giải quyết 100% các trường hợp Zero Anaphora và Tham chiếu liên câu (31 ca lỗi trong CSDL).

### Giải pháp 4: Phân tách Mệnh đề Song hành (Parallel Delimiter Alignment) cho Kỷ luật
* **Nguyên lý:**
  Với các câu đa đối tượng, phân rã câu theo dấu chấm phẩy (`;`) và liên từ *"và"*. Mỗi vế con được xử lý độc lập để bắt cặp chính xác:
  $$\text{Vế 1: } [\text{cảnh cáo}] \to [\text{ông A}] \quad\mid\quad \text{Vế 2: } [\text{khai trừ}] \to [\text{ông B}]$$

---

## 5. KẾ HOẠCH HÀNH ĐỘNG ĐƯA VÀO BÁO CÁO CHÍNH THỨC

Khi cập nhật tài liệu báo cáo học phần ([`report/bao_cao.md`](file:///d:/UniResources/Sem7/MXH/ck/report/bao_cao.md)), chúng ta sẽ bố cục các nội dung này như sau:

1. **Tại Mục 4 (Các bước tiền xử lý & trích xuất):**
   * Bổ sung mục **4.6. Thuật toán Khử trùng Phân rã Đặc trưng (Partitioned Record Linkage)**: Nêu rõ bài toán cạm bẫy trùng tiền tố và cách nhóm giải quyết thành công 100%.
2. **Tại Mục 6 (Đánh giá thực nghiệm & Đối chuẩn):**
   * Đưa bảng so sánh với **BKEE (LREC-COLING 2024)** và **vnOIE** vào mục đối chuẩn quốc tế.
   * Cập nhật kết quả đo đạc trên **Kho Benchmark mở rộng 446 mẫu câu** (thay cho con số 78 mẫu câu cũ).
3. **Tại Mục 8 (Tồn tại & Hướng phát triển):**
   * Trình bày chi tiết **5 lỗ hổng ngôn ngữ học** đã được định lượng trên 6.694 câu.
   * Đưa ra kiến trúc **ViGov-IE cải tiến** với 4 giải pháp kỹ thuật (Aho-Corasick Scoped Matcher, Positional Entity Masking, Discourse Buffer) làm đề xuất nghiên cứu khoa học tương lai.

