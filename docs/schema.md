# Schema mạng Chính trị gia – Cơ quan Quản lý Nhà nước Việt Nam

## Nút

| Nhãn | Thuộc tính | Nguồn |
|---|---|---|
| `Person` | `id`, `name`, `wiki_title`, `wikidata`, `birth_year`, `birth_place`, `hometown`, `status`, `source`, `news_article_count`, `verification_status` | Báo chí; Wikipedia bổ sung hồ sơ |
| `ChucVu` | `id` (pos:<slug chức danh>__<slug cơ quan>), `name` (chức danh chuẩn: "Thứ trưởng"), `org_id`, `org_name`, `hien_thi` ("Thứ trưởng · Bộ Nội vụ"), `kind` (Cấp trưởng / Cấp phó / Thành viên) | Sinh từ (chức danh, cơ quan) của mọi cạnh giữ chức vụ |
| `Organization` | `id` (org:<slug tên>), `name`, `type` (Bộ, UBND tỉnh, Cơ quan Đảng TW, Doanh nghiệp nhà nước...), `level` (TW/Tỉnh), `province` | Infobox + chuẩn hoá tên + config |
| `Province` | `id` (prov:<slug>), `name`, `status` (hiện hành / đã sáp nhập), `valid_from` | config/provinces_2025.json |

Bài báo **không** là nút: URL, ngày và câu bằng chứng được lưu làm thuộc tính cạnh.

**Mô hình 3 lớp:** `(Person)-[:GIU_CHUC_VU {start, end, current}]->(ChucVu)-[:THUOC_CO_QUAN]->(Organization)`.
Mỗi cặp (chức danh, cơ quan) là một nút `ChucVu` dùng chung cho mọi người từng giữ chức đó, nên có thể truy vấn
"ai từng giữ chức Bộ trưởng Bộ Nội vụ" hay chuỗi kế nhiệm theo chức vụ.

## Cạnh

Thuộc tính chung: `role`, `start`, `end`, `current`, `source` (wikipedia:<trang> | rule:... | URL bài báo),
`confidence`, (cạnh từ tin tức thêm `evidence`, `date`, `method`).

### Nhóm A – cạnh có cấu trúc (Wikipedia + quy tắc tổ chức), độ chính xác cao

| Quan hệ | Hướng | Ý nghĩa |
|---|---|---|
| `GIU_CHUC_VU` | Person → ChucVu | Giữ chức vụ từ `start` đến `end` (mỗi nhiệm kỳ một cạnh) |
| `THUOC_CO_QUAN` | ChucVu → Organization | Chức vụ thuộc cơ quan |
| `KE_NHIEM` | Person → Person | A kế nhiệm B ở chức vụ `role` |
| `LANH_DAO_TRUC_TIEP` | Person → Person | A là cấp trên trực tiếp của B (trưởng viên chức trong infobox) |
| `CAP_PHO` | Person → Person | A là cấp phó của B |
| `TRUC_THUOC` | Organization → Organization | Cơ cấu tổ chức (Bộ → Chính phủ, Ban Đảng → BCH TW ...) |
| `THUOC_DIA_PHUONG` | Organization → Province | Cơ quan cấp tỉnh thuộc tỉnh nào |
| `HOP_NHAT_VAO` | Org → Org, Province → Province | Sắp xếp bộ máy / đơn vị hành chính 2025 |
| `NOI_SINH` | Person → Province | Nơi sinh có nguồn rõ ràng; không suy thành quê quán |
| `QUE_QUAN` | Person → Province | Quê quán, chỉ tạo khi nguồn nêu rõ |

### Nhóm B – cạnh trích xuất từ tin tức (NLP, luật), theo yêu cầu đề bài

Sinh bởi `extraction/relations.py`. Mỗi cạnh là **gộp** mọi lần xuất hiện của bộ (nguồn, quan hệ, đích):
`weight` = số câu bằng chứng, `start` = ngày bài sớm nhất, `date` = ngày bài muộn nhất, `evidence` = một câu bằng chứng,
`source` = URL bài, `method` = `rule:<trigger>`, `confidence` ∈ [0.8, 0.9].

| Quan hệ | Hướng | Trigger (ví dụ) | Ràng buộc chính |
|---|---|---|---|
| `CHU_TRI` | Person → Organization | chủ trì (hội nghị, cuộc họp, phiên họp) | cơ quan đứng sau trigger; nếu không có và là cuộc họp → cơ quan trong chức danh của người chủ trì (conf 0.8) |
| `CHI_DAO` | Person → Organization/Person | chỉ đạo, yêu cầu, đề nghị, giao | chủ thể ≤ 45 ký tự trước trigger, đối tượng đứng ngay sau |
| `BO_NHIEM` | Organization/Person → Person | bổ nhiệm, phê chuẩn, chỉ định, phân công | chủ động & bị động ("được Bộ Chính trị … bổ nhiệm"); `to_org`, `role` từ "giữ chức …" |
| `DIEU_DONG` | Organization/Person → Person | điều động, luân chuyển, biệt phái | như trên |
| `MIEN_NHIEM` | Organization/Person → Person | miễn nhiệm, bãi nhiệm, cho thôi giữ chức | như trên |
| `THANH_TRA` | Organization → Organization | thanh tra, kết luận thanh tra, kiểm toán | chủ thể là cơ quan thanh tra/kiểm toán; đích sau "tại/đối với/trách nhiệm của" |
| `KIEM_TRA` | Organization/Person → Organization/Person | kiểm tra, giám sát; "Đoàn kiểm tra … của X … đối với Y" | |
| `KY_LUAT` | Organization/Person → Person | thi hành kỷ luật, cảnh cáo, khiển trách, cách chức, khai trừ | chủ động & bị động, mở rộng danh sách "các ông A, B, C" |
| `LAM_VIEC_VOI` | Person → Organization | làm việc với/tại, thăm và làm việc, hội kiến | |
| `PHOI_HOP` | Organization → Organization | phối hợp với, ký kết quy chế phối hợp | cả dạng "A và B ký kết quy chế phối hợp" |

Ngoài ra từ tin tức còn sinh thêm cạnh nhóm A:
- `GIU_CHUC_VU` từ cụm chức danh đứng cạnh tên ("Bí thư Tỉnh ủy Nghệ An Nguyễn Đức Trung") – chỉ khi Wikipedia chưa có cặp người–cơ quan đó;
  chức danh có "nguyên/cựu/cố" → `current = False`.
- `THUOC_DIA_PHUONG`, `TRUC_THUOC` cho cơ quan cấp tỉnh mới phát hiện (Sở → UBND tỉnh, Công an tỉnh → Bộ Công an, Ban … Tỉnh ủy → Tỉnh ủy).

### Nút bổ sung từ tin tức
- `Person` id `per:news:<slug tên>__<slug tỉnh>`: người **không** có trong gazetteer Wikipedia nhưng xuất hiện kèm chức danh + cơ quan.
  Khoá gồm tỉnh của cơ quan để giảm nhập nhằng trùng tên; `source = news`.
- `Organization` cấp tỉnh tạo theo mẫu tên chuẩn ("Ủy ban nhân dân tỉnh X", "Sở … tỉnh X", "Tỉnh ủy X").

### Liên kết thực thể (extraction/ner_link.py)
1. Cơ quan: khớp dài nhất trên gazetteer + alias viết tắt (UBND, HĐND, Bộ KH&CN, NHNN …) + mẫu cơ quan cấp tỉnh.
2. Người: họ Việt + 1–3 âm tiết viết hoa; nhận nếu khớp **duy nhất** gazetteer (tên ≥ 3 âm tiết hoặc có chức danh);
   trùng tên → chọn người có chức vụ Wikipedia trùng cơ quan trong cụm chức danh; chức vụ cấp tỉnh ở tỉnh người đó chưa từng
   công tác → coi là người khác.
3. Đồng tham chiếu trong bài: tên đã gặp; chức danh đứng một mình ("Thủ tướng yêu cầu…") → người gần nhất giữ chức danh đó
   trong bài (conf 0.85); bỏ qua khi chức danh là nội dung ("giữ chức Thủ tướng") hoặc của nước ngoài ("Thủ tướng Lào …").

## Khử trùng (graph/build_graph.py, chạy trước khi nạp)
- Cơ quan trùng tên chỉ khác hậu tố "Việt Nam", "(Việt Nam)", "nước CHXHCN Việt Nam", kiểu bỏ dấu, hoa/thường -> gộp;
  bỏ các tên chung chung không xác định ("Ủy ban nhân dân tỉnh").
- Cơ quan cấp tỉnh không nêu tỉnh ("Sở Kế hoạch và Đầu tư" trong infobox) -> suy tỉnh từ các chức vụ khác của người đó
  (cùng thời kỳ / cả sự nghiệp ở một tỉnh / chức vụ gần nhất ≤ 3 năm) rồi nối vào cơ quan cụ thể; không suy được ->
  thuộc tính `cu_the = false`, hiển thị "(chưa rõ tỉnh)". Mọi nút `ChucVu` đều có đúng một cạnh `THUOC_CO_QUAN`.
- Chức danh chuẩn hoá: bỏ phần tên cơ quan dính kèm, bỏ "nguyên/tân/cựu/cố", thống nhất hoa/thường.
- `GIU_CHUC_VU`: gộp theo (người, chức vụ, năm bắt đầu); tin tức chỉ thêm nhiệm kỳ khi Wikipedia không có.
- `KE_NHIEM`, `LANH_DAO_TRUC_TIEP`, `CAP_PHO`: một cạnh cho mỗi cặp người (thông tin xuất hiện ở trang của cả hai người,
  `weight` = số nguồn); cặp kế nhiệm mâu thuẫn hai chiều -> giữ chiều có ngày nhậm chức muộn hơn.
- Cạnh còn lại: gộp theo (nguồn, quan hệ, đích), cộng `weight`.

## Thuộc tính hiển thị (graph/cypher/display.cypher)
Sinh tự động sau khi nạp, dùng làm **Caption** trên Neo4j Browser:
- Nút: `hien_thi` – người: "Tên · chức vụ hiện tại" (tối đa 2, ưu tiên Wikipedia), chức vụ: "Thứ trưởng · Bộ Nội vụ",
  cơ quan: tên rút gọn (UBND, HĐND…);
  `chuc_vu` (người) – chức vụ hiện tại, hoặc "nguyên …" nếu không còn chức vụ.
- Cạnh: `nhan` – `GIU_CHUC_VU`: nhiệm kỳ "2021–2025"; cạnh tin tức: "chỉ đạo ×3 · 2026-10"; còn lại: tên tiếng Việt.

## Quy tắc chuẩn hoá thực thể
- Tên cơ quan: bỏ hậu tố "(Việt Nam)", "Đảng Cộng sản Việt Nam"; alias viết tắt (Bộ KH&ĐT, NHNN, EVN...) trong `config/org_mergers_2025.json`.
- Tỉnh: 63 tỉnh cũ giữ làm nút `Province` trạng thái "đã sáp nhập", nối `HOP_NHAT_VAO` tới 34 tỉnh mới.
- Người: định danh theo trang Wikipedia (xử lý trùng tên nhờ trang định hướng); tên không có liên kết chỉ được nối khi khớp **duy nhất** một người trong gazetteer.
- Giai đoạn: chỉ giữ chức vụ còn hiệu lực từ năm 2006 trở đi.
