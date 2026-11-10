"""Find Wikipedia profile candidates for people first recognized in news.

Nguyên tắc:
1. Báo chí là nguồn nòng cốt sinh ra thực thể người và quan hệ.
2. Exact-name search is insufficient for identity verification. Save candidates
   for review; never overwrite graph people from an automatic name match.
3. If Wikipedia has no candidate, the news person remains in the graph.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests
try:
    import mwparserfromhell as mw
except ImportError:
    mw = None

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "processed" / "graph"
PERSON_CSV = GRAPH / "nodes_person.csv"
CANDIDATES_CSV = ROOT / "data" / "processed" / "wiki_enrichment_candidates.csv"

UA = "MXH-VN-Politics-Graph/0.2 (wiki enrichment; contact in repo)"
API = "https://vi.wikipedia.org/w/api.php"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

DATE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
CLEAN_TITLE = re.compile(r"\s*\((?:chính khách|chính trị gia|Việt Nam|sinh \d{4})\)\s*$", re.I)


def _search_wiki(name: str, context: str = "") -> list[dict]:
    """Tìm kiếm trang Wikipedia tiếng Việt theo tên và chức vụ/ngữ cảnh."""
    query = f'"{name}"'
    if context:
        # Lấy từ khoá chính từ context (bỏ dấu nối, lấy cơ quan/chức vụ ngắn)
        ctx_word = context.replace("·", " ").split()[0] if context else ""
        if ctx_word and len(ctx_word) > 2:
            query += f" {ctx_word}"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 5,
        "format": "json",
    }
    try:
        r = SESSION.get(API, params=params, timeout=10)
        if r.status_code == 200:
            return r.json().get("query", {}).get("search", [])
    except requests.RequestException:
        pass
    return []


def _fetch_page_info(title: str) -> dict | None:
    """Tải wikitext và pageprops (Wikidata QID) của 1 trang."""
    params = {
        "action": "query",
        "prop": "revisions|pageprops",
        "rvprop": "content",
        "titles": title,
        "redirects": 1,
        "format": "json",
        "formatversion": 2,
    }
    try:
        r = SESSION.get(API, params=params, timeout=12)
        if r.status_code != 200:
            return None
        pages = r.json().get("query", {}).get("pages", [])
        if not pages or "missing" in pages[0]:
            return None
        page = pages[0]
        wikitext = ""
        if page.get("revisions"):
            wikitext = page["revisions"][0].get("content", "")
        wikidata = (page.get("pageprops") or {}).get("wikibase_item", "")
        return {"title": page["title"], "wikitext": wikitext, "wikidata": wikidata}
    except Exception:
        return None


def _parse_infobox_details(wikitext: str) -> dict:
    """Bóc tách năm sinh, quê quán, thông tin nghỉ hưu từ infobox wikitext."""
    out = {"birth_year": "", "hometown": "", "birth_place": "", "is_retired": False}
    try:
        if mw is not None:
            code = mw.parse(wikitext)
            for t in code.filter_templates():
                t_name = str(t.name).strip().lower()
                if not any(k in t_name for k in ("thông tin", "infobox")):
                    continue
                for param in t.params:
                    name = str(param.name).strip().lower()
                    val = str(param.value).strip()
                    clean_val = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", val)
                    clean_val = re.sub(r"\{\{[^}]+\}\}", "", clean_val).strip()

                    if name in ("ngày sinh", "birth_date", "năm sinh", "sinh") and not out["birth_year"]:
                        years = DATE_YEAR.findall(clean_val)
                        if years:
                            out["birth_year"] = years[0]
                    elif name in ("quê quán", "quê", "hometown") and not out["hometown"]:
                        first_part = clean_val.split("\n")[0].split("<br")[0].strip()
                        if first_part and len(first_part) < 60:
                            out["hometown"] = first_part
                    elif name in ("nơi sinh", "birth_place") and not out["birth_place"]:
                        first_part = clean_val.split("\n")[0].split("<br")[0].strip()
                        if first_part and len(first_part) < 60:
                            out["birth_place"] = first_part
                    elif name in ("kết thúc", "term_end", "năm mất", "death_date"):
                        if clean_val and clean_val.lower() not in ("nay", "đương nhiệm", "hiện tại"):
                            out["is_retired"] = True
        else:
            # Fallback regex thuần không cần thư viện ngoài
            for line in wikitext.splitlines():
                m = re.match(r"^\s*\|\s*([a-zA-Z_À-ỹ\s]+?)\s*=\s*(.+)$", line)
                if not m:
                    continue
                name, val = m.group(1).strip().lower(), m.group(2).strip()
                clean_val = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", val)
                clean_val = re.sub(r"\{\{[^}]+\}\}", "", clean_val).strip()

                if name in ("ngày sinh", "birth_date", "năm sinh", "sinh") and not out["birth_year"]:
                    years = DATE_YEAR.findall(clean_val)
                    if years:
                        out["birth_year"] = years[0]
                elif name in ("quê quán", "quê", "hometown") and not out["hometown"]:
                    first_part = clean_val.split("\n")[0].split("<br")[0].strip()
                    if first_part and len(first_part) < 60:
                        out["hometown"] = first_part
                elif name in ("nơi sinh", "birth_place") and not out["birth_place"]:
                    first_part = clean_val.split("\n")[0].split("<br")[0].strip()
                    if first_part and len(first_part) < 60:
                        out["birth_place"] = first_part
                elif name in ("kết thúc", "term_end", "năm mất", "death_date"):
                    if clean_val and clean_val.lower() not in ("nay", "đương nhiệm", "hiện tại"):
                        out["is_retired"] = True
    except Exception:
        pass
    return out


def enrich_persons(limit: int = 50, dry_run: bool = False):
    if not PERSON_CSV.exists():
        print(f"Không tìm thấy {PERSON_CSV}. Hãy chạy graph/build_graph.py trước.")
        return

    with PERSON_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Only enrich people first discovered in news; old Wiki-only nodes are not targets.
    candidates = []
    for r in rows:
        needs_wiki = (r.get("source") == "news" and
                      (not r.get("wiki_title") or not r.get("birth_year") or not r.get("birth_place")))
        if needs_wiki:
            candidates.append(r)

    print(f"Tổng số người: {len(rows)}, số người cần/có thể bổ sung từ Wikipedia: {len(candidates)}")
    to_process = candidates[:limit]
    candidates_found = []

    for i, p in enumerate(to_process, 1):
        name = p["name"]
        print(f"[{i}/{len(to_process)}] Tra cứu: {name} ({p['id']})...", end=" ", flush=True)

        results = _search_wiki(name)
        matched_title = None
        for res in results:
            t = res["title"]
            base_t = CLEAN_TITLE.sub("", t).strip()
            if base_t.lower() == name.lower():
                matched_title = t
                break

        if not matched_title:
            print("-> Không thấy trang Wiki tương ứng (giữ nguyên nguồn báo chí)")
            time.sleep(0.3)
            continue

        print(f"-> Khớp: '{matched_title}'", end=" ")
        info = _fetch_page_info(matched_title)
        if not info:
            print("(lỗi tải)")
            continue

        details = _parse_infobox_details(info["wikitext"])
        candidates_found.append({"person_id": p["id"], "name": name,
                                 "wiki_title": info["title"], "wikidata": info["wikidata"],
                                 "birth_year": details["birth_year"], "birth_place": details["birth_place"],
                                 "hometown": details["hometown"],
                                 "source_url": "https://vi.wikipedia.org/wiki/" + quote(info["title"].replace(" ", "_")),
                                 "review_status": "candidate"})
        print(f"[Ứng viên cần đối chiếu: sinh {details['birth_year'] or '?'}, nơi sinh: {details['birth_place'] or '?'}, quê: {details['hometown'] or '?'}]")
        time.sleep(0.5)

    print(f"\nKết quả: {len(candidates_found)}/{len(to_process)} ứng viên Wikipedia cần đối chiếu.")
    if not dry_run and candidates_found:
        columns = ["person_id", "name", "wiki_title", "wikidata", "birth_year",
                   "birth_place", "hometown", "source_url", "review_status"]
        with CANDIDATES_CSV.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(candidates_found)
        print(f"Đã lưu ứng viên vào {CANDIDATES_CSV}")


def main():
    parser = argparse.ArgumentParser(description="Làm giàu tri thức người từ Wikipedia theo yêu cầu")
    parser.add_argument("--limit", type=int, default=30, help="Số lượng người tra cứu thử nghiệm")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ tra thử, không lưu bảng ứng viên")
    args = parser.parse_args()
    enrich_persons(limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
