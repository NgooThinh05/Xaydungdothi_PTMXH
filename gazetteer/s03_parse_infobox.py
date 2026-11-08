"""Bước 3 – Bóc tách infobox "Thông tin viên chức" (và các biến thể) từ wikitext.

Đầu vào : data/raw/wikipedia/pages.jsonl
Đầu ra  : data/interim/persons_raw.jsonl – mỗi người 1 dòng:
  {title, name, wikidata, birth_year, birth_place, categories,
   positions: [{idx, title_raw, role, org, org_link, start, end, current,
                superiors[], deputies[], predecessors[], successors[]}]}

Công cụ: mwparserfromhell (phân tích wikitext), regex cho ngày tháng / chức danh.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import mwparserfromhell as mw

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "data" / "raw" / "wikipedia" / "pages.jsonl"
OUT = ROOT / "data" / "interim" / "persons_raw.jsonl"
OUT_ORGS = ROOT / "data" / "interim" / "org_pages.jsonl"

INFOBOX_NAMES = re.compile(r"thông tin (viên chức|chính khách|quân nhân|nhân vật|sĩ quan)|infobox (officeholder|politician|military person|person)", re.I)

# tên tham số (vi / en) -> khoá chuẩn
PARAM_MAP = {
    "chức vụ": "title", "office": "title",
    "bắt đầu": "start", "term_start": "start", "termstart": "start",
    "kết thúc": "end", "term_end": "end", "termend": "end",
    "tiền nhiệm": "predecessors", "predecessor": "predecessors",
    "kế nhiệm": "successors", "successor": "successors",
    "trưởng viên chức": "superiors", "president": "superiors", "primeminister": "superiors",
    "trưởng chức vụ": "superior_role",
    "phó viên chức": "deputies", "deputy": "deputies",
    "phó chức vụ": "deputy_role",
    "địa hạt": "jurisdiction",
}
PARAM_RE = re.compile(r"^(" + "|".join(map(re.escape, sorted(PARAM_MAP, key=len, reverse=True))) + r")[\s_]*(\d*)$", re.I)

# Chức danh (dài trước, ngắn sau) – dùng để tách "chức danh" và "cơ quan"
ROLES = [
    "Thường trực Ban Bí thư", "Tổng Bí thư", "Chủ tịch nước", "Phó Chủ tịch nước", "Phó Thủ tướng Thường trực", "Phó Thủ tướng", "Thủ tướng",
    "Bộ trưởng, Chủ nhiệm", "Bộ trưởng", "Thứ trưởng Thường trực", "Thứ trưởng",
    "Phó Bí thư Thường trực", "Phó Bí thư", "Bí thư",
    "Phó Chủ tịch Thường trực", "Phó Chủ tịch", "Chủ tịch",
    "Phó Chủ nhiệm Thường trực", "Phó Chủ nhiệm", "Chủ nhiệm",
    "Phó Trưởng ban Thường trực", "Phó Trưởng ban", "Trưởng ban",
    "Phó Tổng Giám đốc", "Tổng Giám đốc", "Phó Giám đốc", "Giám đốc",
    "Phó Tổng Thanh tra", "Tổng Thanh tra", "Phó Chánh Thanh tra", "Chánh Thanh tra",
    "Phó Tổng Kiểm toán", "Tổng Kiểm toán", "Phó Thống đốc", "Thống đốc",
    "Phó Chánh án", "Chánh án", "Phó Viện trưởng", "Viện trưởng",
    "Phó Chánh Văn phòng", "Chánh Văn phòng", "Phó Chủ nhiệm Văn phòng", "Chủ nhiệm Văn phòng",
    "Phó Tổng Tham mưu trưởng", "Tổng Tham mưu trưởng", "Phó Chủ nhiệm Tổng cục", "Chủ nhiệm Tổng cục",
    "Phó Tư lệnh", "Tư lệnh", "Phó Chính ủy", "Chính ủy",
    "Phó Tổng cục trưởng", "Tổng cục trưởng", "Phó Cục trưởng", "Cục trưởng", "Phó Vụ trưởng", "Vụ trưởng",
    "Trưởng Đoàn đại biểu Quốc hội", "Phó Trưởng Đoàn đại biểu Quốc hội", "Đại biểu Quốc hội",
    "Phó Tổng Biên tập", "Tổng Biên tập", "Đại sứ", "Ủy viên", "Thành viên", "Trưởng", "Phó",
]
ROLE_RE = re.compile(r"^(" + "|".join(map(re.escape, ROLES)) + r")\b[\s,]*", re.I)

FILE_PREFIX = re.compile(r"^\s*(Tập[ _]tin|File|Hình|Image)\s*:", re.I)
DATE_DMY = re.compile(r"(\d{1,2})\s*tháng\s*(\d{1,2})\D{0,12}?(\d{4})")
DATE_MY = re.compile(r"tháng\s*(\d{1,2})\D{0,12}?(\d{4})")
YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
CURRENT = re.compile(r"\b(nay|đương nhiệm|hiện tại|incumbent)\b", re.I)
VN_NAME = re.compile(r"^[A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,4}$")
DISAMBIG = re.compile(r"\s*\((chính khách|Việt Nam|chính trị gia|sinh \d{4}|\d{4})\)\s*$")


def strip_files(code: mw.wikicode.Wikicode) -> mw.wikicode.Wikicode:
    for link in code.filter_wikilinks(recursive=False):
        if FILE_PREFIX.match(str(link.title)):
            try:
                code.remove(link)
            except ValueError:
                pass
    return code


def plain(value) -> str:
    raw = re.sub(r"<br\s*/?>", "\n", str(value), flags=re.I)
    code = strip_files(mw.parse(raw))
    txt = code.strip_code(normalize=True, collapse=True)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", txt).strip(" ,;*")


def first_line(value) -> tuple[str, str]:
    """Ô 'chức vụ' hay có dạng 'Chức vụ<br>khóa XIV / phụ trách ...' -> (dòng chính, ghi chú)."""
    raw = re.sub(r"<br\s*/?>", "\n", str(value), flags=re.I)
    code = strip_files(mw.parse(raw))
    txt = re.sub(r"<[^>]+>", " ", code.strip_code(normalize=True, collapse=False))
    parts = [re.sub(r"[ \t]+", " ", p).strip(" ,;*") for p in txt.split("\n")]
    parts = [p for p in parts if p]
    return (parts[0], " | ".join(parts[1:])) if parts else ("", "")


def links(value) -> list[tuple[str, str]]:
    out = []
    for l in mw.parse(str(value)).filter_wikilinks():
        t = str(l.title).strip().replace("_", " ")
        if FILE_PREFIX.match(t) or t.startswith(("Thể loại:", ":")) or "#" in t[:1]:
            continue
        out.append((t.split("#")[0].strip(), str(l.text).strip() if l.text else t))
    return out


def parse_date(value) -> tuple[str | None, bool]:
    raw = str(value)
    # Mẫu {{số năm theo năm và ngày|y|m|d|...}} chỉ là bộ đếm -> bỏ, đọc phần chữ
    raw_no_tpl = re.sub(r"\{\{\s*số năm[^}]*\}\}", " ", raw, flags=re.I)
    txt = plain(raw_no_tpl)
    if CURRENT.search(txt):
        return None, True
    m = DATE_DMY.search(txt)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}", False
    m = DATE_MY.search(txt)
    if m:
        mo, y = m.groups()
        return f"{y}-{int(mo):02d}", False
    m = YEAR.search(txt)
    return (m.group(1), False) if m else (None, False)


def person_list(value) -> list[dict]:
    """Danh sách người trong ô tiền nhiệm / kế nhiệm / cấp trên / cấp phó."""
    res, seen = [], set()
    for target, text in links(value):
        name = DISAMBIG.sub("", text if VN_NAME.match(text.strip()) else target).strip()
        if VN_NAME.match(name) and target not in seen:
            seen.add(target)
            res.append({"name": name, "link": target})
    # tên không có liên kết: tách theo *, <br>, xuống dòng, dấu phẩy
    rest = mw.parse(str(value))
    for l in rest.filter_wikilinks():
        try:
            rest.remove(l)
        except ValueError:
            pass
    txt = re.sub(r"<br\s*/?>|\*|\n|;|,", "|", str(rest), flags=re.I)
    for part in txt.split("|"):
        p = re.sub(r"\(.*?\)|''+|\{\{.*?\}\}", "", plain(part)).strip()
        if VN_NAME.match(p) and p not in seen:
            seen.add(p)
            res.append({"name": p, "link": None})
    return res


def split_role_org(title_raw: str, title_links: list[tuple[str, str]]) -> tuple[str, str, str | None]:
    """'Bộ trưởng Bộ Nội vụ' -> ('Bộ trưởng', 'Bộ Nội vụ', 'Bộ Nội vụ (Việt Nam)')."""
    txt = title_raw
    role = ""
    m = ROLE_RE.match(txt)
    if m:
        role = m.group(1)
        org = txt[m.end():].strip(" ,")
    else:
        org = txt
    org_link = None
    for target, _ in title_links:
        tm = ROLE_RE.match(target)
        if tm:  # liên kết tới bài về chức vụ: "Chủ tịch Ủy ban nhân dân Thành phố Hà Nội"
            if not role:
                role = tm.group(1)
            cand = target[tm.end():].strip(" ,")
            if cand and not org:
                org = cand
            continue
        org_link = target
        break
    org = re.sub(r"\s*\((thường trực|Thường trực|quyền|Quyền)\)\s*", " ", org).strip()
    # "Tổng Kiểm toán Nhà nước", "Tổng Thanh tra Chính phủ": chức danh chứa tên cơ quan
    if org in ("Nhà nước", "Chính phủ") and re.search(r"(Kiểm toán|Thanh tra)$", role):
        org = role.split()[-2] + " " + role.split()[-1] + " " + org
    return role, org, org_link


def find_infobox(code):
    for t in code.filter_templates(recursive=False):
        if INFOBOX_NAMES.search(str(t.name)):
            return t
    for t in code.filter_templates(recursive=False):  # fallback: template có tham số chức vụ
        if any(PARAM_RE.match(str(p.name).strip()) for p in t.params):
            return t
    return None


def parse_person(page: dict) -> dict | None:
    code = mw.parse(page["wikitext"])
    box = find_infobox(code)
    if box is None:
        return None
    slots: dict[str, dict] = {}
    info = {}
    for p in box.params:
        key = str(p.name).strip()
        m = PARAM_RE.match(key)
        if m:
            slots.setdefault(m.group(2) or "0", {})[PARAM_MAP[m.group(1).lower()]] = p.value
        else:
            info[key.lower()] = p.value
    positions = []
    for idx, s in sorted(slots.items(), key=lambda kv: int(kv[0])):
        if "title" not in s or not plain(s["title"]):
            continue
        title_raw, note = first_line(s["title"])
        if not title_raw:
            continue
        # tách hậu tố nhiệm kỳ: "Trung ương Đảng khóa XI (dự khuyết), XII" -> term
        term = ""
        tm = re.search(r"\s*\bkh(?:óa|oá|oa)\s+[IVXL].*$", title_raw)
        if tm:
            term, title_raw = tm.group(0).strip(), title_raw[:tm.start()].strip()
        if not term:
            tm = re.search(r"\bkh(?:óa|oá|oa)\s+[IVXL][^|]*", note)
            term = tm.group(0).strip() if tm else ""
        role, org, org_link = split_role_org(title_raw, links(s["title"]))
        start, _ = parse_date(s.get("start", ""))
        end, current = parse_date(s.get("end", ""))
        if not s.get("end") or not plain(s.get("end", "")):
            current = current or False
        positions.append({
            "idx": int(idx), "title_raw": title_raw, "note": note, "term": term,
            "role": role, "org": org, "org_link": org_link,
            "start": start, "end": end, "current": current,
            "superior_role": plain(s.get("superior_role", "")),
            "superiors": person_list(s.get("superiors", "")),
            "deputies": person_list(s.get("deputies", "")),
            "predecessors": person_list(s.get("predecessors", "")),
            "successors": person_list(s.get("successors", "")),
            "jurisdiction": plain(s.get("jurisdiction", "")),
        })
    by = YEAR.search(str(info.get("ngày sinh", info.get("birth_date", ""))))
    name = plain(info.get("tên", "")) or DISAMBIG.sub("", page["title"])
    return {
        "title": page["title"], "name": DISAMBIG.sub("", name), "wikidata": page.get("wikidata"),
        "pageid": page.get("pageid"),
        "birth_year": int(by.group(1)) if by else None,
        "birth_place": plain(info.get("nơi sinh", info.get("birth_place", "")))[:200],
        "categories": page.get("categories", []),
        "wiki_categories": [str(l.title).replace("Thể loại:", "").strip()
                            for l in code.filter_wikilinks() if str(l.title).strip().startswith("Thể loại:")],
        "positions": positions,
    }


def main():
    n_in = n_ok = n_org = 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with INP.open(encoding="utf-8") as f, OUT.open("w", encoding="utf-8") as fo, \
            OUT_ORGS.open("w", encoding="utf-8") as fg:
        for line in f:
            page = json.loads(line)
            n_in += 1
            if page["kind"] == "org":
                fg.write(json.dumps({k: page[k] for k in ("title", "wikidata", "pageid", "categories")},
                                    ensure_ascii=False) + "\n")
                n_org += 1
                continue
            rec = parse_person(page)
            if rec and rec["positions"]:
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_ok += 1
    print(f"{n_in} trang -> {n_ok} người có infobox chức vụ, {n_org} trang tổ chức")


if __name__ == "__main__":
    main()
