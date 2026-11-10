# Pipeline báo chí và kỹ thuật trích xuất

Tài liệu này phân biệt rõ phần **đang chạy trong mã nguồn** với phần mở rộng
đang được chuẩn bị. Wikipedia chỉ dùng làm gazetteer/định danh ban đầu; bằng
chứng cho sự kiện được lấy từ bài báo và lưu kèm URL, ngày, câu nguồn.

## 1. Thu thập dữ liệu

### Crawl theo chuyên mục và từ khóa cố định

`crawler/crawl_news.py` thu thập:

- Báo Chính phủ: timeline Chính trị, Chỉ đạo - quyết định và 19 truy vấn cho
  quan hệ hiếm;
- VnExpress: Thời sự/Chính trị và Nhân sự.

Trang danh sách được tải bằng `requests`, URL bài được lấy bằng regex, nội dung
chính và metadata được bóc bằng `trafilatura`. Có tối đa 4 luồng tải bài, ba lần
thử lại, timeout kết nối/đọc, độ dài tối thiểu 300 ký tự và checkpoint theo URL.

### Crawl theo khoảng trống thực thể

`crawler/crawl_targeted.py` không quét vô hạn. Lệnh `plan` đọc đồ thị cuối và
chọn người/cơ quan chưa có cạnh sự kiện. Với mỗi thực thể nó sinh ba nhóm truy
vấn:

- hành động: chỉ đạo, giao, chủ trì, bổ nhiệm, điều động, miễn nhiệm, kỷ luật,
  kiểm tra, thanh tra, phối hợp;
- văn bản: ký/ban hành quyết định, quyết định/nghị quyết/chỉ thị/công văn/kết
  luận/thông báo có số;
- gia đình (chỉ với người): cha, mẹ, vợ, chồng, con, anh/chị/em.

Lệnh `crawl` mặc định khám phá URL qua Google News RSS và giải mã về URL bài
gốc bằng HTTP; backend Bing RSS và tìm kiếm Báo
Chính phủ có thể bật thủ công nhưng không dùng mặc định vì trang hiện tải kết
quả bằng JavaScript. Crawler chỉ chấp nhận danh sách domain báo chí/cổng chính thức, kiểm tra `robots.txt`,
giới hạn tốc độ theo host, lọc khoảng ngày và yêu cầu tên mục tiêu xuất hiện
trong bài. Mỗi bản ghi lưu thêm `target_id`, loại truy vấn, câu truy vấn, backend
khám phá và thời điểm tải để kiểm toán.

```powershell
python crawler/crawl_targeted.py plan --people 50 --orgs 50
python crawler/crawl_targeted.py crawl --max-queries 20 --pages 1 --dry-run
python crawler/crawl_targeted.py crawl --max-queries 20 --pages 1
```

## 2. Chuẩn hóa corpus

`preprocess/build_corpus.py` đọc tự động mọi JSONL do crawler tạo, cùng corpus
Báo Mới và `5k_scrawl` nếu có. Các bước gồm:

1. chuẩn hóa Unicode NFC, kiểu đặt dấu và khoảng trắng;
2. đổi timestamp/ngày về ISO `YYYY-MM-DD`;
3. khử trùng theo URL và tiêu đề chuẩn hóa;
4. gộp danh sách mục tiêu nếu một bài được nhiều truy vấn tìm thấy;
5. bỏ tiêu đề lặp đầu nội dung;
6. tách câu bằng regex có bảo vệ chữ viết tắt tiếng Việt;
7. giữ provenance của crawl có mục tiêu trong corpus.

## 3. Nhận diện và liên kết thực thể

`extraction/ner_link.py` dùng phương pháp lai dựa trên từ điển và luật:

| Nhiệm vụ | Kỹ thuật đang dùng | Mục đích |
|---|---|---|
| Cơ quan | Gazetteer, alias, khớp chuỗi dài nhất | Chuẩn hóa UBND/HĐND/tên bộ về cùng ID |
| Cơ quan địa phương | Regex loại cơ quan + tỉnh | Phát hiện Sở, Tỉnh ủy, Công an tỉnh chưa có trong gazetteer |
| Người | Mẫu họ tên Việt Nam + vùng viết hoa | Sinh ứng viên tên người |
| Liên kết người | Khớp duy nhất, chức danh-cơ quan, tỉnh công tác | Giảm nhập nhằng người trùng tên |
| Người mới | Tên + chức danh + cơ quan/tỉnh | Tạo ID ổn định cho người chỉ xuất hiện trong báo |
| Đồng vị ngữ | Phân tích chuỗi chức danh trước/sau tên | Tách người giữ chức gì tại cơ quan nào |
| Đồng tham chiếu | Bộ nhớ trong phạm vi bài | Nối “Thủ tướng”, “Bộ trưởng” với tên đã nêu |
| Loại nhiễu | Mẫu đường, trường, tư tưởng, nước ngoài | Tránh coi địa danh/tổ chức là người |

Đây không phải NER học máy. `rapidfuzz` có trong dependencies nhưng pipeline
trích xuất chính hiện ưu tiên khớp chuẩn/alias và luật để giữ precision.

## 4. Trích xuất quan hệ

`extraction/relations.py` áp dụng luật có kiểu thực thể. Mỗi luật gồm trigger,
kiểu chủ thể/đối tượng, cửa sổ ký tự, đoạn chèn hợp lệ và mẫu loại trừ. Thuật
toán xử lý:

- câu chủ động và bị động;
- tác nhân trong cụm “quyết định của X”;
- danh sách nhiều người;
- phủ định `không/chưa`;
- trigger nằm trong từ khác (`giao` trong `Ngoại giao`);
- chức danh/cơ quan đã được hấp thụ vào cụm tên;
- chức vụ và cơ quan đích sau bổ nhiệm/điều động.

Mười quan hệ sự kiện hiện tại là `CHU_TRI`, `CHI_DAO`, `BO_NHIEM`,
`DIEU_DONG`, `MIEN_NHIEM`, `THANH_TRA`, `KIEM_TRA`, `KY_LUAT`,
`LAM_VIEC_VOI`, `PHOI_HOP`. Tin tức còn sinh `GIU_CHUC_VU` từ cụm đồng vị ngữ.

Mỗi lần trích lưu `doc_id`, chỉ số câu, văn bản câu, trigger, hai span thực thể,
URL, ngày, chiều bị động và confidence của luật. Khi dựng đồ thị, các lần cùng
`(src, rel, dst)` đang được gộp thành một cạnh và cộng `weight`.

## 5. Phân tích chất lượng và độ phủ

Các phép kiểm đang dùng:

- lấy mẫu phân tầng theo loại quan hệ;
- precision và khoảng tin cậy Wilson 95%;
- thống kê câu chứa trigger so với câu trích được làm chỉ báo độ phủ;
- kiểm tra đầu mút, ID trùng, self-loop và khóa cạnh trùng;
- thống kê số người/cơ quan có ít nhất một cạnh sự kiện;
- phân bố theo nguồn, năm và loại quan hệ.

Hiện chưa đo recall chuẩn vì chưa có tập câu được gán nhãn toàn bộ quan hệ.
Quan hệ họ hàng và thực thể văn bản cũng chưa được trích; crawler mới chỉ thu
thêm ứng viên cho hai nhóm này. Trước khi đưa vào Neo4j cần thiết kế `Event`,
`Document`, `Article` và bộ nhãn đánh giá riêng.

### Dữ liệu bổ sung từ repository bên ngoài

Bộ `NgooThinh05/Xaydungdothi_PTMXH` được lưu riêng tại
`data/external/xaydungdothi_ptmxh`, kèm commit và mô tả nguồn. Corpus Báo Mới
5.325 bài của bộ này trùng corpus đang có nên không được nhập lần hai. Script
`preprocess/audit_github_supplement.py` chỉ đối chiếu hồ sơ/cạnh đồng xuất hiện
và xuất bảng ứng viên. Đồng xuất hiện không được đổi thành `CHI_DAO`, quan hệ
gia đình hay quan hệ tổ chức nếu không có câu bằng chứng tương ứng.

Tương tự, `query_kind`/`query_kinds` của crawler chỉ ghi lý do một URL được
phát hiện, không phải nhãn quan hệ. Đặc biệt kết quả truy vấn gia đình phải có
câu bằng chứng nêu rõ hai người và loại quan hệ trước khi sinh cạnh họ hàng.

## 6. Tỉnh/cơ quan theo thời gian

### Ghi chú vận hành mới: giữ người chưa có quan hệ và tách các lần trích sự kiện

`extraction/relations.py` ghi `person_mentions_news.csv` cho mọi người được linker
xác nhận trong bài và đưa mọi người mới đã nhận diện vào `nodes_person_news.csv`,
kể cả khi chưa khớp luật quan hệ. `crawler/crawl_targeted.py plan` ưu tiên những
người đã được nhắc trong báo nhưng còn ít cạnh sự kiện; truy vấn bao gồm sự kiện,
văn bản, gia đình và tiểu sử. Bài crawl bổ sung phải chứa tên mục tiêu; nếu chức danh
đã thay đổi, bài vẫn được lưu với `target_match=name_only` để rà soát trùng tên.
Những bài này chưa nhập corpus. Khi ngữ cảnh chức danh/địa phương khớp,
trường này là `context` và bài có thể đi tiếp vào bước trích xuất.

`python extraction/family.py` chỉ tạo ứng viên `PARENT_OF`, `SPOUSE_OF`,
`SIBLING_OF` khi một câu có đúng hai tên đã định danh và cụm quan hệ rõ ràng.
Ứng viên được gắn `review_status=candidate`; không suy quan hệ từ việc cùng
xuất hiện. Nếu nguồn hiện tại không có câu đủ điều kiện, file cạnh sẽ rỗng.

Nơi sinh trong infobox Wikipedia đi vào `birth_place`/`NOI_SINH`, không đi vào
`hometown`/`QUE_QUAN`. `gazetteer/enrich_wiki.py` chỉ xuất bảng ứng viên
`wiki_enrichment_candidates.csv` để đối chiếu định danh; cùng tên không đủ để
tự ghi thuộc tính Wiki vào người trong graph.

Mỗi lần trích quan hệ sự kiện có `event_id` ổn định theo bài, chỉ số câu, loại
quan hệ, hai đầu mút và trigger. `event_date` chỉ được điền khi câu bằng chứng có
ngày đầy đủ; `date` vẫn là ngày đăng bài. Cùng cặp thực thể có thể có nhiều cạnh
cùng loại khi xuất hiện trong các câu/bài khác nhau. Đây là các *lần trích có
bằng chứng*, chưa phải các sự kiện thực tế đã được hợp nhất xuyên nguồn; cần
đối chiếu văn bản, ngày và thực thể trước khi coi nhiều lần trích là một sự kiện.

Bài báo phải liên kết theo ngày sự kiện, không thay tên lịch sử bằng tên hiện
hành. Thiết kế mục tiêu là:

- `ProvinceVersion`/`OrganizationVersion`: tên và ID có hiệu lực trong một
  khoảng thời gian;
- `current_area_id`: khóa quy đổi để tổng hợp theo 34 tỉnh hiện hành;
- bảng ánh xạ có `from_id`, `to_id`, `effective_date`, `mapping_type`, nguồn;
- ưu tiên ngày sự kiện, sau đó ngày văn bản, cuối cùng mới dùng ngày đăng bài.

Ánh xạ hành chính không được tính như quan hệ xã hội trong PageRank, bậc hay
phát hiện cộng đồng.
