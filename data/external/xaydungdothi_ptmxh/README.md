# Dữ liệu bổ sung từ Xaydungdothi_PTMXH

- Nguồn: `https://github.com/NgooThinh05/Xaydungdothi_PTMXH`
- Nhánh: `main`
- Commit đã tải: `93f8358f86edfef8803af6d20e922271da6c7659`
- Ngày tải: 2026-11-10 (Asia/Saigon)
- Cách nhập: `git fetch` rồi trích chọn lọc bằng `git archive`; không merge nhánh
  nguồn vì lịch sử dự án khác và nhánh nguồn xóa nhiều file của pipeline hiện tại.

## Nội dung

- `baomoi_political_corpus.jsonl`: 5.325 bài Báo Mới, 03/02/2025–08/11/2026.
- `baomoi_persons_political_table.csv`: lượt nhắc người theo bài.
- `baomoi_vn_politicians_profiles.csv`: hồ sơ tổng hợp theo tên.
- `baomoi_vn_politicians_edges.csv`: quan hệ đồng xuất hiện.
- `neo4j_import/`: các bảng nút/cạnh do dự án nguồn xuất cho Neo4j.
- Các script gốc được giữ để kiểm toán cách tạo dữ liệu.

## Kiểm tra trùng

Corpus 5.325 bài trùng với corpus Báo Mới đang có trong workspace (5.324 URL
khớp trực tiếp, bài còn lại cũng không tạo URL hoặc tiêu đề mới). Vì vậy không
đưa corpus này vào `news_docs.jsonl` lần thứ hai. Giá trị bổ sung chính là bảng
hồ sơ, vai trò, cơ quan và đồng xuất hiện để làm ứng viên đối chiếu.

Các ID và quan hệ trong thư mục này chưa được coi là dữ liệu chuẩn. Chỉ nhập
vào đồ thị sau khi liên kết thực thể với ID hiện hành và kiểm tra câu bằng chứng.
