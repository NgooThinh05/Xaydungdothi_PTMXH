"""Client nhỏ cho MediaWiki API (vi.wikipedia.org) và Wikidata SPARQL.

- Giới hạn tốc độ (mặc định ~1 request/giây) + tự retry khi gặp 429/5xx.
- Cache trên đĩa (data/raw/...) để chạy lại không phải tải lại.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import requests

UA = "MXH-VN-Politics-Graph/0.1 (https://github.com/NgooThinh05/Xaydungdothi_PTMXH; student coursework)"
VIWIKI_API = "https://vi.wikipedia.org/w/api.php"
WDQS = "https://query.wikidata.org/sparql"
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "raw" / "cache"


class Throttled:
    def __init__(self, min_interval: float = 0.5):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        self.min_interval = min_interval
        self._last = 0.0

    def get(self, url: str, params: dict, timeout: int = 90) -> requests.Response:
        for attempt in range(8):
            wait = self.min_interval - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            try:
                r = self.s.get(url, params=params, timeout=timeout)
            except requests.RequestException:
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                retry = r.headers.get("Retry-After")
                time.sleep(float(retry) if retry and retry.isdigit() else 10 * (attempt + 1))
                continue
            r.raise_for_status()
        raise RuntimeError(f"Failed after retries: {url} {params}")


_http = Throttled()


def _cached(kind: str, key: str, fn):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{kind}_{hashlib.md5(key.encode()).hexdigest()}.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:  # file dở dang do bị ngắt -> tải lại
            f.unlink()
    data = fn()
    tmp = f.with_suffix(".tmp")  # ghi file tạm rồi đổi tên: không bao giờ để lại cache hỏng
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(f)
    return data


def wiki_api(**params) -> dict:
    params.update(format="json", formatversion=2, maxlag=5)
    key = json.dumps(params, sort_keys=True, ensure_ascii=False)
    return _cached("wiki", key, lambda: _http.get(VIWIKI_API, params).json())


def sparql(query: str) -> list[dict]:
    def run():
        r = _http.get(WDQS, {"query": query, "format": "json"}, timeout=180)
        out = []
        for b in r.json()["results"]["bindings"]:
            out.append({k: v["value"].replace("http://www.wikidata.org/entity/", "") for k, v in b.items()})
        return out
    return _cached("wdqs", query, run)


def category_members(cat: str, cmtype: str = "page|subcat") -> list[dict]:
    """Toàn bộ thành viên của một thể loại (tự phân trang)."""
    out, cont = [], {}
    while True:
        d = wiki_api(action="query", list="categorymembers", cmtitle=cat,
                     cmtype=cmtype, cmlimit=500, **cont)
        out += d["query"]["categorymembers"]
        if "continue" not in d:
            return out
        cont = {"cmcontinue": d["continue"]["cmcontinue"]}


REDIRECTS: dict[str, str] = {}  # tiêu đề gốc / redirect -> tiêu đề đích


def wikitext_batch(titles: list[str]) -> dict[str, dict]:
    """Lấy wikitext + pageid + wikidata id cho tối đa 50 tiêu đề/lần (tự theo redirect).
    Các cặp redirect/chuẩn hoá tiêu đề được ghi vào REDIRECTS."""
    res = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        d = wiki_api(action="query", prop="revisions|pageprops", rvprop="content", rvslots="main",
                     ppprop="wikibase_item", redirects=1, titles="|".join(chunk))
        for key in ("normalized", "redirects"):
            for r in d["query"].get(key, []):
                REDIRECTS[r["from"]] = r["to"]
        for p in d["query"].get("pages", []):
            if "revisions" not in p:
                continue
            res[p["title"]] = {
                "pageid": p["pageid"],
                "wikidata": p.get("pageprops", {}).get("wikibase_item"),
                "wikitext": p["revisions"][0]["slots"]["main"]["content"],
            }
    return res
