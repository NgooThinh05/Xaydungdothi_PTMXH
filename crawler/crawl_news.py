"""Crawl tin Thời sự - Chính trị theo chuyên mục và từ khóa cố định.

Nguồn trực tiếp: Báo Chính phủ và VnExpress. Crawler theo khoảng trống thực thể
nằm ở ``crawler/crawl_targeted.py``.

Đầu ra: ``data/raw/news/<site>.jsonl``. Mỗi dòng có ``site``, ``url``,
``title``, ``date``, ``sapo`` và ``text``. Chạy lại an toàn: URL đã thành công
hoặc đã thất bại được bỏ qua.
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

UA = "MXH-VN-Politics-Graph/0.2 (student research; contact in repository)"
WORKERS = 4
DELAY = 1.0
MIN_TEXT = 300
MIN_YEAR = 2024

SITES = {
    "baochinhphu": {
        "pages": [f"https://baochinhphu.vn/timelinelist/{z}/{{n}}.htm" for z in (102442, 1023)],
        "link": r'href="(/[a-z0-9-]+-\d{15,}\.htm)"',
        "base": "https://baochinhphu.vn",
        "max_pages": 300,
    },
    "baochinhphu_search": {
        "pages": [f"https://baochinhphu.vn/tim-kiem.htm?keywords={quote(k)}&page={{n}}" for k in (
            "kết luận thanh tra", "Thanh tra Chính phủ thanh tra", "Kiểm toán Nhà nước kiểm toán",
            "Ủy ban Kiểm tra Trung ương", "thi hành kỷ luật", "cảnh cáo", "khiển trách",
            "khai trừ ra khỏi Đảng", "miễn nhiệm", "cho thôi giữ chức", "kiểm tra, giám sát đối với",
            "Đoàn kiểm tra", "Đoàn giám sát", "điều động, bổ nhiệm", "điều động, chỉ định",
            "phối hợp ký kết quy chế", "trao quyết định bổ nhiệm", "chủ trì hội nghị",
            "làm việc với Ban Thường vụ Tỉnh ủy")],
        "link": r'href="(/[a-z0-9-]+-\d{15,}\.htm)"',
        "base": "https://baochinhphu.vn",
        "max_pages": 40,
        "no_year_stop": True,
    },
    "vnexpress": {
        "pages": ["https://vnexpress.net/thoi-su/chinh-tri-p{n}",
                  "https://vnexpress.net/thoi-su/chinh-tri/nhan-su-p{n}"],
        "link": r'href="(https://vnexpress\.net/[a-z0-9-]+-\d{7}\.html)"',
        "base": "",
        "max_pages": 150,
    },
    "vietnamnet": {
        "pages": ["https://vietnamnet.vn/chinh-tri-page{n}"],
        "link": r'href="(/[a-z0-9-]+-\d+\.html)"',
        "base": "https://vietnamnet.vn",
        "max_pages": 100,
    },
    "dantri": {
        "pages": ["https://dantri.com.vn/thoi-su/chinh-tri/trang-{n}.htm"],
        "link": r'href="((?:https://dantri\.com\.vn)?/thoi-su/[a-z0-9-]+-\d{14,}\.htm)"',
        "base": "https://dantri.com.vn",
        "max_pages": 100,
    },
}

sess = requests.Session()
sess.headers.update({"User-Agent": UA, "Accept-Language": "vi-VN,vi;q=0.9"})
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def get(url: str) -> str | None:
    for attempt in range(3):
        try:
            r = sess.get(url, timeout=(8, 25))
            if r.status_code == 200:
                r.encoding = r.apparent_encoding or "utf-8"
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
    return url, {"title": d.get("title"), "date": d.get("date"),
                 "sapo": d.get("description"), "text": d.get("text")}


def _read_seen(path: Path) -> set[str]:
    out = set()
    if not path.exists():
        return out
    for line in path.open(encoding="utf-8", errors="ignore"):
        try:
            value = json.loads(line)
            if isinstance(value, dict) and value.get("url"):
                out.add(value["url"])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return out


def crawl(site: str):
    cfg = SITES[site]
    out_path = OUT_DIR / f"{site}.jsonl"
    fail_path = OUT_DIR / f"{site}.failed.txt"
    seen = _read_seen(out_path)
    n_have = len(seen)
    if fail_path.exists():
        seen.update(x.strip() for x in fail_path.open(encoding="utf-8") if x.strip())
    print(f"[{site}] đã có {n_have} bài", flush=True)
    with out_path.open("a", encoding="utf-8") as out, fail_path.open("a", encoding="utf-8") as fail, \
            ThreadPoolExecutor(WORKERS) as pool:
        t0 = time.time()
        for tmpl in cfg["pages"]:
            empty = stale = 0
            for n in range(1, cfg["max_pages"] + 1):
                html = get(tmpl.format(n=n))
                raw_links = re.findall(cfg["link"], html or "")
                links = list(dict.fromkeys(x if x.startswith("http") else cfg["base"] + x for x in raw_links))
                if not links:
                    empty += 1
                    if empty >= 3:
                        break
                    continue
                empty = 0
                new = [u for u in links if u not in seen]
                seen.update(new)
                ok = old = 0
                for url, art in pool.map(extract, new):
                    if not art:
                        fail.write(url + "\n")
                        continue
                    year = (art["date"] or "")[:4]
                    if year.isdigit() and int(year) < MIN_YEAR:
                        old += 1
                    out.write(json.dumps({"site": site, "url": url, **art}, ensure_ascii=False) + "\n")
                    ok += 1
                    n_have += 1
                out.flush()
                fail.flush()
                print(f"[{site}] {n_have:5d} bài +{ok:2d} "
                      f"{(time.time() - t0) / 60:5.1f} phút {tmpl.format(n=n)}", flush=True)
                stale = stale + 1 if not new else 0
                if stale >= 3:
                    break
                if not cfg.get("no_year_stop") and new and old == ok and ok > 0:
                    print(f"[{site}] gặp bài trước {MIN_YEAR}, dừng chuyên mục", flush=True)
                    break
                time.sleep(DELAY)
    print(f"[{site}] xong: {n_have} bài", flush=True)


if __name__ == "__main__":
    for source in (sys.argv[1:] or list(SITES)):
        if source not in SITES:
            raise SystemExit(f"Nguồn không hợp lệ: {source}. Chọn: {', '.join(SITES)}")
        crawl(source)
