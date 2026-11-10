"""Crawl có mục tiêu cho người/cơ quan còn thiếu bằng chứng báo chí.

Hai bước tách biệt để kiểm soát phạm vi:

1. ``plan`` đọc đồ thị cuối, tìm thực thể chưa có cạnh sự kiện và sinh truy vấn.
2. ``crawl`` dùng Google News RSS để khám phá URL đa nguồn; trang tìm kiếm Báo
   Chính phủ vẫn có thể bật thủ công để kiểm thử nhưng không dùng mặc định vì
   trang HTML hiện tải kết quả bằng JavaScript.
   URL từ danh sách báo cho phép, sau đó tải bài gốc bằng trafilatura.

Crawler lưu cả ``target_id``, truy vấn và backend khám phá để truy vết vì sao
mỗi bài được thu thập. Nó không sửa CSV đồ thị; chạy ``build_corpus.py`` và
``relations.py`` sau khi rà soát dữ liệu thô.
"""
from __future__ import annotations

import argparse
import csv
import email.utils
import json
import re
import sys
import time
import urllib.parse
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import requests
import trafilatura

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "processed" / "graph"
RAW = ROOT / "data" / "raw" / "news"
PLAN = ROOT / "data" / "interim" / "crawl_targets.jsonl"
OUT = RAW / "targeted_news.jsonl"
FAIL = RAW / "targeted_news.failed.jsonl"

UA = "MXH-VN-Politics-Graph/0.2 (student research; contact in repository)"
EVENT_RELS = {
    "CHU_TRI", "PHOI_HOP", "LAM_VIEC_VOI", "CHI_DAO", "BO_NHIEM",
    "THANH_TRA", "KIEM_TRA", "DIEU_DONG", "KY_LUAT", "MIEN_NHIEM",
}
ALLOWED_DOMAINS = {
    "baochinhphu.vn", "xaydungchinhsach.chinhphu.vn", "nhandan.vn",
    "baotintuc.vn", "vnanet.vn", "quochoi.vn", "daibieunhandan.vn",
    "qdnd.vn", "cand.vn", "vnexpress.net", "thanhnien.vn", "tuoitre.vn",
    "vietnamnet.vn", "dantri.com.vn", "tienphong.vn", "laodong.vn",
    "congly.vn", "phapluatplus.vn", "vietnamplus.vn", "sggp.org.vn",
    "hanoimoi.vn", "congthuong.vn", "baoxaydung.vn", "baovanhoa.vn",
}
RELATION_TERMS = (
    "chỉ đạo", "yêu cầu", "giao", "chủ trì", "bổ nhiệm", "điều động",
    "miễn nhiệm", "kỷ luật", "kiểm tra", "thanh tra", "phối hợp",
)
DOCUMENT_TERMS = (
    "ký quyết định", "ban hành quyết định", "quyết định số", "nghị quyết số",
    "chỉ thị số", "công văn số", "kết luận số", "thông báo số",
)
FAMILY_TERMS = (
    "con trai", "con gái", "vợ", "chồng", "cha", "mẹ", "bố", "anh trai",
    "chị gái", "em trai", "em gái",
)
BIOGRAPHY_TERMS = ("tiểu sử", "quê quán", "sinh tại", "nơi sinh", "quá trình công tác")
RETIRED_TERMS = (
    "nguyên", "cựu", "nghỉ hưu", "thôi giữ chức", "kỷ luật", "kết luận", "vi phạm", "xóa tư cách",
)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Language": "vi-VN,vi;q=0.9"})
ROBOTS: dict[str, urllib.robotparser.RobotFileParser] = {}
LAST_REQUEST: dict[str, float] = defaultdict(float)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _entity_relation_counts(edges: list[dict], event_only: bool = True) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for e in edges:
        if event_only and e["rel"] not in EVENT_RELS:
            continue
        counts[e["src"]] += 1
        counts[e["dst"]] += 1
    return counts


def _person_context(edges: list[dict], positions: dict[str, dict]) -> dict[str, tuple[list[str], int, bool]]:
    out: dict[str, list[tuple[int, str, bool]]] = defaultdict(list)
    for e in edges:
        if e["rel"] != "GIU_CHUC_VU" or e["dst"] not in positions:
            continue
        p = positions[e["dst"]]
        start_year = int(e["start"][:4]) if (e.get("start") or "")[:4].isdigit() else 0
        end_year = int(e["end"][:4]) if (e.get("end") or "")[:4].isdigit() else 0
        current = e.get("current") == "True"
        is_retired = (not current) and (end_year > 0 and end_year < 2024 or (e.get("role") or "").startswith("nguyên"))
        score = (6 if current else 3 if start_year >= 2022 or end_year >= 2022 else 2)
        score += 1 if p.get("level") == "TW" else 0
        out[e["src"]].append((score, p.get("hien_thi") or p["name"], is_retired))

    res = {}
    for k, v in out.items():
        ctx_list = [x[1] for x in sorted(v, reverse=True)[:2]]
        max_score = max(x[0] for x in v)
        is_ret = all(x[2] for x in v)
        res[k] = (ctx_list, max_score, is_ret)
    return res


def _queries(target: dict) -> list[dict]:
    name = target["name"]
    context = target.get("context", "")
    suffix = f' "{context}"' if context else ""
    result = [
        {"kind": "event", "query": f'"{name}" ({" OR ".join(RELATION_TERMS)}){suffix}'},
        {"kind": "document", "query": f'"{name}" ({" OR ".join(DOCUMENT_TERMS)}){suffix}'},
    ]
    if target.get("is_retired"):
        result.append({"kind": "retired", "query": f'"{name}" ({" OR ".join(RETIRED_TERMS)}){suffix}'})
    if target["entity_type"] == "Person":
        result.append({"kind": "family", "query": f'"{name}" ({" OR ".join(FAMILY_TERMS)}){suffix}'})
        result.append({"kind": "biography", "query": f'"{name}" ({" OR ".join(BIOGRAPHY_TERMS)}){suffix}'})
    return result


def build_plan(limit_people: int, limit_orgs: int, min_relations: int = 5, event_only: bool = True) -> list[dict]:
    people = read_csv(GRAPH / "nodes_person.csv")
    orgs = read_csv(GRAPH / "nodes_org.csv")
    positions = {x["id"]: x for x in read_csv(GRAPH / "nodes_position.csv")}
    edges = read_csv(GRAPH / "edges.csv")
    rel_counts = _entity_relation_counts(edges, event_only=event_only)
    contexts = _person_context(edges, positions)
    mention_path = ROOT / "data" / "processed" / "person_mentions_news.csv"
    news_mentioned = ({r["person_id"] for r in read_csv(mention_path)}
                      if mention_path.exists() else set())

    # Ưu tiên người có ít quan hệ (< min_relations). Càng ít quan hệ thì càng ưu tiên crawl bù.
    person_rows = []
    for p in people:
        if news_mentioned and p["id"] not in news_mentioned:
            continue
        cnt = rel_counts.get(p["id"], 0)
        if cnt >= min_relations:
            continue
        ctx_info = contexts.get(p["id"])
        if ctx_info:
            ctx, score, is_ret = ctx_info
            ctx_str = ctx[0] if ctx else ""
        else:
            ctx_str = p.get("hometown", "")
            score = 1
            is_ret = (p.get("status") == "đã về hưu")

        # Càng ít quan hệ (< 5) thì priority càng lớn để kéo lên đầu
        article_count = int(p.get("news_article_count") or 0)
        priority = ((min_relations - cnt) * 10 + score + min(article_count, 10) * 3
                    + (30 if p.get("verification_status") == "needs_review" else 0))
        person_rows.append({
            "entity_id": p["id"], "entity_type": "Person", "name": p["name"],
            "context": ctx_str, "current_relations": cnt, "is_retired": is_ret,
            "news_article_count": article_count, "priority": priority,
        })
    person_rows.sort(key=lambda x: (-x["priority"], x["name"]))

    # Cơ quan có ít quan hệ (< min_relations)
    org_rows = []
    for o in orgs:
        cnt = rel_counts.get(o["id"], 0)
        if cnt >= min_relations or not o.get("name"):
            continue
        priority = (min_relations - cnt) * 5 + (3 if o.get("level") == "Tỉnh" else 2 if o.get("level") == "TW" else 1)
        org_rows.append({
            "entity_id": o["id"], "entity_type": "Organization", "name": o["name"],
            "context": o.get("province", ""), "current_relations": cnt, "priority": priority,
        })
    org_rows.sort(key=lambda x: (-x["priority"], x["name"]))

    targets = person_rows[:limit_people] + org_rows[:limit_orgs]
    rows = []
    for target in targets:
        for q in _queries(target):
            rows.append({**target, **q})
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    with PLAN.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Kế hoạch: {len(targets)} thực thể (< {min_relations} quan hệ), {len(rows)} truy vấn -> {PLAN}")
    print(f"  người thiếu quan hệ: {min(limit_people, len(person_rows))}/{len(person_rows)} (ưu tiên người ít quan hệ nhất)")
    print(f"  cơ quan thiếu quan hệ: {min(limit_orgs, len(org_rows))}/{len(org_rows)}")
    return rows


def _host(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def _allowed(url: str) -> bool:
    host = _host(url)
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)


def _get(url: str, *, delay: float = 1.0, timeout=(8, 30)) -> requests.Response | None:
    host = _host(url)
    wait = delay - (time.time() - LAST_REQUEST[host])
    if wait > 0:
        time.sleep(wait)
    for attempt in range(3):
        try:
            response = SESSION.get(url, timeout=timeout)
            LAST_REQUEST[host] = time.time()
            if response.status_code == 200:
                return response
            if response.status_code in (404, 410):
                return None
            if response.status_code == 429 or response.status_code >= 500:
                time.sleep(3 * (attempt + 1))
                continue
            return None
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
    return None


def _robots_allowed(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin not in ROBOTS:
        robot = urllib.robotparser.RobotFileParser(origin + "/robots.txt")
        try:
            response = SESSION.get(origin + "/robots.txt", timeout=(5, 15))
            if response.status_code == 200:
                robot.parse(response.text.splitlines())
            elif response.status_code in (401, 403):
                robot.parse(["User-agent: *", "Disallow: /"])
            else:
                robot.parse(["User-agent: *", "Allow: /"])
        except requests.RequestException:
            # Không xác minh được robots thì không tự động tải bài từ host đó.
            robot.parse(["User-agent: *", "Disallow: /"])
        ROBOTS[origin] = robot
    return ROBOTS[origin].can_fetch(UA, url)


def discover_baochinhphu(target_name: str, kind: str, pages: int) -> list[dict]:
    # Tìm kiếm nội bộ của Báo Chính phủ không hiểu cú pháp OR/ngoặc như công
    # cụ tìm kiếm web; dùng truy vấn ngắn để tránh nó trả trang tin mới nhất.
    suffix = {"event": "chỉ đạo", "document": "quyết định", "family": "gia đình",
              "biography": "tiểu sử", "retired": "nghỉ hưu"}[kind]
    query = f'"{target_name}" {suffix}'
    found = []
    for page in range(1, pages + 1):
        url = "https://baochinhphu.vn/tim-kiem.htm?" + urllib.parse.urlencode({"keywords": query, "page": page})
        response = _get(url)
        if response is None:
            break
        links = re.findall(r'href=["\'](/[a-z0-9-]+-\d{15,}\.htm)["\']', response.text)
        if not links:
            break
        found.extend({"url": "https://baochinhphu.vn" + x, "backend": "baochinhphu_search"} for x in links)
    return list({x["url"]: x for x in found}.values())


def _unwrap_bing_url(url: str) -> str:
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    for key in ("url", "u", "r"):
        if key in q and q[key]:
            value = urllib.parse.unquote(q[key][0])
            if value.startswith("http"):
                return value
    return url


def discover_bing(query: str, pages: int) -> list[dict]:
    # Bing News cung cấp RSS công khai; ``pages`` được đổi thành số kết quả tối đa.
    count = min(100, max(10, pages * 20))
    url = "https://www.bing.com/news/search?" + urllib.parse.urlencode({
        "q": query, "format": "rss", "setlang": "vi-vn", "count": count,
    })
    response = _get(url)
    if response is None:
        return []
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError:
        return []
    found = []
    for item in root.findall(".//item"):
        link = item.findtext("link") or ""
        link = _unwrap_bing_url(link)
        if not link.startswith("http") or not _allowed(link):
            continue
        published = item.findtext("pubDate") or ""
        try:
            dt = email.utils.parsedate_to_datetime(published)
            published = dt.date().isoformat()
        except (TypeError, ValueError):
            published = ""
        found.append({"url": link, "backend": "bing_news_rss",
                      "discovered_title": item.findtext("title") or "",
                      "discovered_date": published})
    return list({x["url"]: x for x in found}.values())


def _decode_google_news_url(news_url: str) -> str | None:
    """Đổi URL RSS Google News thành URL bài gốc bằng endpoint batchexecute.

    Google RSS không đặt URL gốc trong XML. Trang ``rss/articles/<id>`` cung
    cấp timestamp và signature; endpoint batchexecute trả URL nguồn. Cách này
    chỉ dùng HTTP/regex/JSON nên chạy được trên Windows bị chặn DLL ngoài.
    """
    parsed = urllib.parse.urlparse(news_url)
    parts = parsed.path.rstrip("/").split("/")
    if parsed.hostname != "news.google.com" or len(parts) < 2 or parts[-2] not in ("articles", "read"):
        return None
    article_id = parts[-1]
    params_url = (f"https://news.google.com/rss/articles/{article_id}?"
                  + urllib.parse.urlencode({"hl": "vi", "gl": "VN", "ceid": "VN:vi"}))
    response = _get(params_url, delay=0.3)
    if response is None:
        return None
    signature = re.search(r'data-n-a-sg="([^"]+)"', response.text)
    timestamp = re.search(r'data-n-a-ts="([^"]+)"', response.text)
    if not signature or not timestamp:
        return None
    context = [
        ["X", "X", ["X", "X"], None, None, 1, 1, "VN:vi", None, 1,
         None, None, None, None, None, 0, 1],
        "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0,
    ]
    inner = ["garturlreq", context, article_id, int(timestamp.group(1)), signature.group(1)]
    envelope = [[["Fbv4je", json.dumps(inner, separators=(",", ":")), None, "0"]]]
    body = "f.req=" + urllib.parse.quote(json.dumps(envelope, separators=(",", ":")))
    try:
        decoded = SESSION.post(
            "https://news.google.com/_/DotsSplashUi/data/batchexecute",
            headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
            data=body, timeout=(8, 30),
        )
        decoded.raise_for_status()
        text = decoded.text
        if "\n\n" in text:
            text = text.split("\n\n", 1)[1]
        text = text.lstrip()
        if text.startswith(")]}'"):
            text = text.split("\n", 1)[1] if "\n" in text else text[4:]
        rows = json.loads(text.lstrip())
        for row in rows:
            if not isinstance(row, list) or len(row) < 3 or not isinstance(row[2], str):
                continue
            payload = json.loads(row[2])
            if isinstance(payload, list) and len(payload) > 1 and payload[0] == "garturlres":
                return payload[1]
    except (requests.RequestException, json.JSONDecodeError, TypeError, ValueError, IndexError):
        return None
    return None


def discover_google(query: str, pages: int) -> list[dict]:
    count = min(100, max(10, pages * 20))
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query, "hl": "vi", "gl": "VN", "ceid": "VN:vi", "num": count,
    })
    response = _get(url, delay=0.3)
    if response is None:
        return []
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError:
        return []
    target = query.split('"')[1].casefold() if '"' in query else query.casefold()
    candidates = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        source = item.find("source")
        source_home = source.get("url", "") if source is not None else ""
        if target not in title.casefold() or not _allowed(source_home):
            continue
        published = item.findtext("pubDate") or ""
        try:
            published = email.utils.parsedate_to_datetime(published).date().isoformat()
        except (TypeError, ValueError):
            published = ""
        candidates.append((item.findtext("link") or "", title, published))
    found = []
    for news_url, title, published in candidates[:10]:
        original = _decode_google_news_url(news_url)
        if original and _allowed(original):
            found.append({"url": original, "backend": "google_news_rss",
                          "discovered_title": title, "discovered_date": published})
    return list({x["url"]: x for x in found}.values())


def _bing_query(row: dict) -> str:
    # RSS cho kết quả tốt hơn với truy vấn ngắn; ngữ cảnh chức vụ được kiểm
    # lại trong toàn văn sau khi tải để phân biệt người trùng tên.
    suffix = {"event": "chỉ đạo", "document": "quyết định", "family": "gia đình",
              "biography": "tiểu sử", "retired": "nghỉ hưu"}[row["kind"]]
    return f'"{row["name"]}" {suffix}'


def _existing_urls() -> set[str]:
    seen = set()
    for path in RAW.rglob("*.jsonl"):
        if ".failed." in path.name:
            continue
        for line in path.open(encoding="utf-8", errors="ignore"):
            try:
                value = json.loads(line)
                if isinstance(value, dict) and value.get("url"):
                    seen.add(value["url"])
            except json.JSONDecodeError:
                continue
    return seen


def _extract_article(item: dict, min_date: date, max_date: date) -> dict | None:
    url = item["url"]
    if not _allowed(url) or not _robots_allowed(url):
        return None
    response = _get(url)
    if response is None:
        return None
    try:
        doc = trafilatura.bare_extraction(response.text, url=url, with_metadata=True)
    except Exception:
        return None
    doc = doc.as_dict() if doc else None
    if not doc or len(doc.get("text") or "") < 300:
        return None
    raw_date = (doc.get("date") or item.get("discovered_date") or "")[:10]
    try:
        article_date = date.fromisoformat(raw_date)
    except ValueError:
        article_date = None
    if article_date and not min_date <= article_date <= max_date:
        return None
    haystack = f"{doc.get('title') or ''}\n{doc.get('text') or ''}".lower()
    if item["target_name"].lower() not in haystack:
        return None
    # Tên người Việt thường trùng nhau. Với mục tiêu Person, bắt buộc bài còn
    # chứa ngữ cảnh chức vụ/cơ quan; nếu không sẽ dễ lấy nhầm ca sĩ, vận động
    # viên hoặc người cùng tên. Dùng từng vế quanh dấu "·" để không đòi hỏi
    # nguyên cụm chức danh phải xuất hiện đúng từng ký tự.
    context = (item.get("target_context") or "").lower()
    target_match = "name_only"
    if item["target_type"] == "Person" and context:
        clues = [x.strip() for x in re.split(r"[·;]", context) if len(x.strip()) >= 6]
        place = re.search(r"(?:tỉnh|thành phố)\s+[\wÀ-ỹ ]{3,35}$", context)
        if any(clue in haystack for clue in clues) or (place and place.group(0) in haystack):
            target_match = "context"
        # A previous office can change; keep name-only hits as review candidates.
    return {
        "site": _host(url), "url": url, "title": doc.get("title"), "date": raw_date,
        "sapo": doc.get("description"), "text": doc.get("text"),
        "target_id": item["target_id"], "target_name": item["target_name"],
        "target_type": item["target_type"], "target_context": item.get("target_context", ""),
        "target_match": target_match,
        "query_kind": item["query_kind"],
        "query": item["query"], "discovery_backend": item["backend"],
        "query_kinds": item.get("query_kinds", [item["query_kind"]]),
        "queries": item.get("queries", [item["query"]]),
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def crawl(args):
    if not PLAN.exists():
        raise SystemExit(f"Chưa có {PLAN}; chạy lệnh plan trước.")
    rows = [json.loads(x) for x in PLAN.open(encoding="utf-8") if x.strip()]
    rows = rows[args.start_query:args.start_query + args.max_queries]
    seen = _existing_urls()
    discovered: dict[str, dict] = {}
    backends = set(args.backends)
    for i, row in enumerate(rows, 1):
        hits = []
        if "baochinhphu" in backends:
            hits += discover_baochinhphu(row["name"], row["kind"], args.pages)
        if "bing" in backends:
            hits += discover_bing(_bing_query(row), args.pages)
        if "google" in backends:
            # Dùng truy vấn ngắn theo từng loại thay vì chỉ tên người. Nếu chỉ
            # tìm tên, ba nhóm event/document/family trả cùng một tập kết quả.
            hits += discover_google(_bing_query(row), args.pages)
        for hit in hits:
            if hit["url"] in seen:
                continue
            if hit["url"] in discovered:
                current = discovered[hit["url"]]
                if row["kind"] not in current["query_kinds"]:
                    current["query_kinds"].append(row["kind"])
                if row["query"] not in current["queries"]:
                    current["queries"].append(row["query"])
                continue
            discovered[hit["url"]] = {
                **hit, "target_id": row["entity_id"], "target_name": row["name"],
                "target_type": row["entity_type"], "target_context": row.get("context", ""),
                "query_kind": row["kind"], "query": row["query"],
                "query_kinds": [row["kind"]], "queries": [row["query"]],
            }
        print(f"[{i}/{len(rows)}] {row['name']}: {len(hits)} URL, mới {len(discovered)}", flush=True)
    if args.dry_run:
        print(f"Dry-run: khám phá {len(discovered)} URL; chưa tải bài.")
        return

    RAW.mkdir(parents=True, exist_ok=True)
    min_date = date.fromisoformat(args.from_date)
    max_date = date.fromisoformat(args.to_date)
    saved = failed = 0
    with OUT.open("a", encoding="utf-8") as out, FAIL.open("a", encoding="utf-8") as fail:
        for i, item in enumerate(discovered.values(), 1):
            article = _extract_article(item, min_date, max_date)
            if article:
                out.write(json.dumps(article, ensure_ascii=False) + "\n")
                out.flush()
                saved += 1
            else:
                fail.write(json.dumps({"url": item["url"], "target_id": item["target_id"],
                                       "reason": "blocked_or_not_relevant"}, ensure_ascii=False) + "\n")
                fail.flush()
                failed += 1
            print(f"  tải [{i}/{len(discovered)}] lưu {saved}, bỏ {failed}", flush=True)
    print(f"Hoàn tất: +{saved} bài -> {OUT}; bỏ {failed}")


def parse_args():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="Sinh danh sách truy vấn từ khoảng trống đồ thị")
    plan.add_argument("--people", type=int, default=50, help="Số người ưu tiên")
    plan.add_argument("--orgs", type=int, default=50, help="Số cơ quan ưu tiên")
    plan.add_argument("--min-relations", type=int, default=5,
                      help="Ngưỡng quan hệ tối thiểu (mặc định < 5 quan hệ thì đưa vào kế hoạch crawl)")
    plan.add_argument("--all-relations", action="store_true",
                      help="Tính toàn bộ quan hệ (mặc định chỉ tính quan hệ sự kiện)")
    run = sub.add_parser("crawl", help="Khám phá URL và tải bài")
    run.add_argument("--backends", nargs="+", choices=("google", "baochinhphu", "bing"),
                     default=("google",))
    run.add_argument("--max-queries", type=int, default=20)
    run.add_argument("--start-query", type=int, default=0,
                     help="Bỏ qua N truy vấn đầu để chạy tiếp theo từng lô")
    run.add_argument("--pages", type=int, default=1)
    run.add_argument("--from-date", default="2022-01-01")
    run.add_argument("--to-date", default=datetime.now().date().isoformat())
    run.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    cli = parse_args()
    if cli.command == "plan":
        build_plan(cli.people, cli.orgs, min_relations=cli.min_relations, event_only=not cli.all_relations)
    else:
        crawl(cli)
