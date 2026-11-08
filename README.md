# Mạng lưới Chính trị gia & Cơ quan Quản lý Nhà nước Việt Nam

Đồ thị tri thức kết nối lãnh đạo bộ ngành / địa phương với cơ quan nhà nước và tập đoàn trọng điểm,
xây dựng từ Wikipedia tiếng Việt và tin tức Thời sự – Nội chính, lưu trong **Neo4j**.
Schema chi tiết: [docs/schema.md](docs/schema.md).

## Cấu trúc thư mục

```
config/        alias cơ quan, sáp nhập bộ ngành & tỉnh 2025
gazetteer/     thu thập + bóc tách Wikipedia -> nút/cạnh khung + gazetteer cho NER
crawler/       crawl tin tức (Báo Mới, Báo Chính phủ, VnExpress, ...)
preprocess/    làm sạch, tách câu, lọc câu ứng viên
extraction/    NER + liên kết thực thể + trích xuất quan hệ (rule -> PhoBERT)
graph/         schema Cypher + script nạp Neo4j
stats/         thống kê mạng -> report/stats.md, report/figures/
data/          raw/ (không đưa lên git), interim/, processed/ (CSV nạp Neo4j)
```

## Cài đặt

```bash
conda create -n mxh python=3.11 -y && conda activate mxh
pip install -r requirements.txt
cp .env.example .env
docker compose up -d          # Neo4j 5.26 + APOC + GDS, Browser: http://localhost:7474
```

## Chạy pipeline

```bash
# 1) Khung mạng từ Wikipedia
cd gazetteer
python s01_collect_pages.py   # duyệt cây thể loại -> danh sách trang
python s02_fetch_pages.py     # tải wikitext (+ Wikidata QID)
python s03_parse_infobox.py   # bóc tách infobox "Thông tin viên chức"
python s04_build_gazetteer.py # chuẩn hoá, sinh nodes_*.csv / edges_wiki.csv / gazetteer_*.json
# (tuỳ chọn) vòng mở rộng: chạy lại s02 -> s03 -> s04 để tải các người được liên kết trong infobox
cd ..

# 2) Tin tức: crawl bổ sung -> gộp corpus -> NER + liên kết thực thể + trích quan hệ bằng luật
#    (corpus Báo Mới của nhóm đặt tại data/raw/news/baomoi/baomoi_political_corpus.jsonl)
python crawler/crawl_news.py                 # baochinhphu, baochinhphu_search, vnexpress -> data/raw/news/*.jsonl
python preprocess/build_corpus.py            # -> data/interim/news_docs.jsonl (khử trùng, tách câu)
python extraction/relations.py               # -> data/processed/edges_news.csv, nodes_*_news.csv, data/eval/sample_to_label.csv

# 3) Nạp Neo4j & thống kê
python graph/load_neo4j.py --reset
python stats/graph_stats.py

# 4) Đánh giá: điền cột label (1/0) trong data/eval/sample_to_label.csv rồi
python extraction/evaluate.py                # -> report/eval_precision.md
```

## Công cụ
| Việc | Công cụ |
|---|---|
| Thu thập Wikipedia | MediaWiki Action API (`requests`, giới hạn tốc độ + cache) |
| Bóc tách wikitext / infobox | `mwparserfromhell`, regex |
| Chuẩn hoá thực thể | `unicodedata` (NFC), từ điển alias, `rapidfuzz` |
| Crawl tin tức | `requests`, `BeautifulSoup`, `trafilatura` |
| NLP tiếng Việt (bài giữa kỳ) | Không dùng thư viện ngoài: chuẩn hoá dấu + tách câu bằng regex, NER bằng gazetteer + mẫu tên/chức danh, trích quan hệ bằng luật (`extraction/`) |
| NLP tiếng Việt (bài cuối kỳ, dự kiến) | PhoBERT (`vinai/phobert-base-v2`) phân loại quan hệ, học từ nhãn luật + nhãn thủ công |
| CSDL đồ thị | Neo4j 5.26 Community + APOC + Graph Data Science (Docker) |
| Thống kê / hình | `networkx`, `matplotlib`, Neo4j Browser |
