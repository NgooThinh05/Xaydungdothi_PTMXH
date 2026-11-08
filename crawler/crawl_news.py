"""Crawl bổ sung tin Thời sự – Chính trị cho trích xuất quan hệ.

Nguồn: Báo Chính phủ (baochinhphu.vn, API timeline theo chuyên mục) và VnExpress (Thời sự > Chính trị).
Đầu ra: data/raw/news/<site>.jsonl  – mỗi dòng {site, url, title, date, sapo, text}
Chạy lại được: bỏ qua URL đã có / đã lỗi.

    python crawler/crawl_news.py                 # mọi nguồn
    python crawler/crawl_news.py baochinhphu     # một nguồn
"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from urllib.parse import quote

import requests
import trafilatura

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw" / "news"
OUT_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
WORKERS = 4
DELAY = 1.0          # nghỉ giữa các trang danh sách (giây)
MIN_TEXT = 300
MIN_YEAR = 2024      # dừng chuyên mục khi một trang toàn bài cũ hơn năm này

SITES = {
    "baochinhphu": {
        # 102442 = Chính trị, 1023 = Chỉ đạo – quyết định của Chính phủ, Thủ tướng
        "pages": [f"https://baochinhphu.vn/timelinelist/{z}/{{n}}.htm" for z in (102442, 1023)],
        "link": r'href="(/[a-z0-9-]+-\d{15,}\.htm)"',
        "base": "https://baochinhphu.vn",
        "max_pages": 300,
    },
    # Tìm kiếm theo từ khoá cho các loại quan hệ hiếm (thanh tra, kiểm tra, kỷ luật, miễn nhiệm, điều động)
    "baochinhphu_search": {
        "pages": [f"https://baochinhphu.vn/tim-kiem.htm?keywords={quote(k)}&page={{n}}" for k in (
            "kết luận thanh tra", "Thanh tra Chính phủ thanh tra", "Kiểm toán Nhà nước kiểm toán", "Ủy ban Kiểm tra Trung ương",
            "thi hành kỷ luật", "cảnh cáo", "khiển trách", "khai trừ ra khỏi Đảng", "miễn nhiệm", "cho thôi giữ chức",
            "kiểm tra, giám sát đối với", "Đoàn kiểm tra", "Đoàn giám sát", "điều động, bổ nhiệm", "điều động, chỉ định",
            "phối hợp ký kết quy chế", "trao quyết định bổ nhiệm", "chủ trì hội nghị", "làm việc với Ban Thường vụ Tỉnh ủy")],
        "link": r'href="(/[a-z0-9-]+-\d{15,}\.htm)"',
        "base": "https://baochinhphu.vn",
        "max_pages": 40,
        "no_year_stop": True,
    },
    "vnexpress": {
        "pages": ["https://vnexpress.net/thoi-su/chinh-tri-p{n}", "https://vnexpress.net/thoi-su/chinh-tri/nhan-su-p{n}"],
        "link": r'href="(https://vnexpress\.net/[a-z0-9-]+-\d{7}\.html)"',
        "base": "",
        "max_pages": 150,
    },
}

sess = requests.Session()
sess.headers.update({"User-Agent": UA, "Accept-Language": "vi-VN,vi;q=0.9"})


def get(url: str) -> str | None:
    for attempt in range(3):
        try:
            r = sess.get(url, timeout=(8, 25))
            if r.status_code == 200:
                r.encoding = "utf-8"
                return r.text
            if r.status_code in (404, 410):
                return None
        except requests.RequestException:
            pass
        time.sleep(3 * (attempt + 1))
    return None


def extract(url: str):
    html = get(url)
    if not html:
        return url, None
    try:
        d = trafilatura.bare_extraction(html, url=url, with_metadata=True)
    except Exception:
        return url, None
    d = d.as_dict() if d else None
    if not d or len(d.get("text") or "") < MIN_TEXT:
        return url, None
    return url, {"title": d.get("title"), "date": d.get("date"), "sapo": d.get("description"), "text": d.get("text")}


def crawl(site: str):
    cfg = SITES[site]
    out_path, fail_path = OUT_DIR / f"{site}.jsonl", OUT_DIR / f"{site}.failed.txt"
    seen = set()
    if out_path.exists():
        seen |= {json.loads(l)["url"] for l in out_path.open(encoding="utf-8")}
    n_have = len(seen)
    if fail_path.exists():
        seen |= {l.strip() for l in fail_path.open(encoding="utf-8")}
    print(f"[{site}] đã có {n_have} bài", flush=True)
    out, fail = out_path.open("a", encoding="utf-8"), fail_path.open("a", encoding="utf-8")
    pool = ThreadPoolExecutor(WORKERS)
    t0 = time.time()
    for tmpl in cfg["pages"]:
        empty = stale = 0
        for n in range(1, cfg["max_pages"] + 1):
            html = get(tmpl.format(n=n))
            links = list(dict.fromkeys(cfg["base"] + l for l in re.findall(cfg["link"], html or "")))
            if not links:
                empty += 1
                if empty >= 3:
                    break
                continue
            empty = 0
            new = [u for u in links if u not in seen]
            seen.update(new)
            ok, old = 0, 0
            for url, art in pool.map(extract, new):
                if not art:
                    fail.write(url + "\n")
                    continue
                y = (art["date"] or "")[:4]
                if y.isdigit() and int(y) < MIN_YEAR:
                    old += 1
                out.write(json.dumps({"site": site, "url": url, **art}, ensure_ascii=False) + "\n")
                ok += 1
                n_have += 1
            out.flush(); fail.flush()
            print(f"[{site}] {n_have:5d} bài  +{ok:2d}  {(time.time() - t0) / 60:5.1f} phút  {tmpl.format(n=n)}", flush=True)
            stale = stale + 1 if not new else 0
            if stale >= 3:  # trang tìm kiếm chỉ lặp lại kết quả cũ -> hết
                break
            if not cfg.get("no_year_stop") and new and old == ok and ok > 0:  # cả trang toàn bài cũ -> sang chuyên mục khác
                print(f"[{site}] gặp bài trước {MIN_YEAR}, dừng chuyên mục", flush=True)
                break
            time.sleep(DELAY)
    out.close(); fail.close()
    print(f"[{site}] xong: {n_have} bài", flush=True)


if __name__ == "__main__":
    for s in (sys.argv[1:] or list(SITES)):
        crawl(s)
