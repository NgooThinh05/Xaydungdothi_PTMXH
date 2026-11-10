"""Dựng bảng đồ thị cuối cùng (khử trùng + mô hình 3 lớp Người – Chức vụ – Cơ quan) để nạp Neo4j.

Đầu vào : data/processed/nodes_*.csv, edges_wiki.csv, edges_news.csv
Đầu ra  : data/processed/graph/nodes_person.csv, nodes_org.csv, nodes_position.csv, nodes_province.csv, edges.csv

Các bước:
 1. Gộp cơ quan trùng tên (khác nhau ở hậu tố "Việt Nam", "(Việt Nam)", "nước CHXHCN Việt Nam", kiểu bỏ dấu, hoa/thường);
    bỏ các "cơ quan" chung chung không xác định được (vd "Ủy ban nhân dân tỉnh").
 2. Chuẩn hoá chức danh: bỏ phần tên cơ quan dính kèm ("Chủ tịch Ủy ban nhân dân tỉnh Gia Lai" -> "Chủ tịch"),
    bỏ tiền tố nguyên/tân/cựu/cố (-> cờ), thống nhất hoa/thường ("Trưởng Ban" -> "Trưởng ban").
 3. Mô hình 3 lớp: (Person)-[:GIU_CHUC_VU {start,end,...}]->(ChucVu)-[:THUOC_CO_QUAN]->(Organization).
    Mỗi cặp (chức danh, cơ quan) là MỘT nút ChucVu, dùng chung cho mọi người từng giữ chức đó.
 4. Khử trùng cạnh:
    - GIU_CHUC_VU: gộp theo (người, chức vụ, năm bắt đầu); tin tức chỉ bổ sung khi Wikipedia không có nhiệm kỳ đó.
    - KE_NHIEM / LANH_DAO_TRUC_TIEP / CAP_PHO: một cạnh cho mỗi cặp người (thông tin này được ghi ở trang Wikipedia
      của CẢ HAI người); cặp KE_NHIEM mâu thuẫn hai chiều -> giữ chiều có ngày nhậm chức muộn hơn (người kế nhiệm).
    - Cạnh sự kiện từ báo: giữ từng event_id để không gộp các lần trích khác nhau.
    - Cạnh cấu trúc khác: gộp theo (nguồn, quan hệ, đích), cộng weight.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "extraction"))
from ner_link import ALL_TITLES, HISTORICAL_OR_FOREIGN  # noqa: E402
from textnorm import norm_text, slug  # noqa: E402

PROC = ROOT / "data" / "processed"
OUT = PROC / "graph"


def read(name: str) -> list[dict]:
    p = PROC / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def write(name: str, rows: list[dict], fields: list[str]):
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------------ 1. cơ quan
GENERIC_ORG_KEYS = {"ủy ban nhân dân tỉnh", "ủy ban nhân dân thành phố", "hội đồng nhân dân tỉnh",
                    "hội đồng nhân dân thành phố", "ủy ban nhân dân", "hội đồng nhân dân", "tổng cục", "ủy ban kiểm tra",
                    "đảng ủy", "ủy ban kiểm tra đảng ủy", "sở", "công an", "ủy ban", "ban chỉ đạo", "ủy ban nhân dân tỉnh việt nam"}
KEEP_LONG = ("Hội ", "Ngân hàng", "Bộ đội", "Tập đoàn", "Tổng Liên đoàn", "Thông tấn", "Đài ", "Liên hiệp", "Học viện",
             "Tổng công ty", "Mặt trận", "Bảo hiểm", "Kho bạc")


def org_key(name: str) -> str:
    n = norm_text(name).lower().replace("–", "-")
    n = re.sub(r"\s*\((?:việt nam|nước|tỉnh|thành phố)\)", "", n)
    n = re.sub(r"\s+nước cộng hòa xã hội chủ nghĩa việt nam$", "", n)
    n = re.sub(r"\s+(?:đảng cộng sản việt nam|việt nam)$", "", n)
    n = re.sub(r"^(ban bí thư|bộ chính trị)\s+(?:ban chấp hành\s+)?trung ương(?:\s+đảng)?$", r"\1", n)
    n = re.sub(r"\s*-\s*", " ", n)                                   # "Giao thông - Vận tải" = "Giao thông vận tải"
    n = re.sub(r"(?<!\w)tp\.?\s*(?=\w)", "thành phố ", n)             # "TP Hồ Chí Minh" = "thành phố Hồ Chí Minh"
    n = re.sub(r"thành phố (?:hcm|thành phố hồ chí minh)\b", "thành phố hồ chí minh", n)
    return re.sub(r"\s+", " ", n).strip()


# ------------------------------------------------------------------ 1b. tỉnh của cơ quan
_PC = json.loads((ROOT / "config" / "provinces_2025.json").read_text(encoding="utf-8"))
CENTRAL = set(_PC["central_cities"]) | {"Thành phố Hồ Chí Minh"}
PROV_ALIAS = {**_PC["aliases"], "Hồ Chí Minh": "Thành phố Hồ Chí Minh", "TP.HCM": "Thành phố Hồ Chí Minh",
              "TPHCM": "Thành phố Hồ Chí Minh", "HCM": "Thành phố Hồ Chí Minh"}
PROV_NAMES = sorted({n for v in _PC["merge"].values() for n in v} | set(_PC["merge"]) | set(PROV_ALIAS),
                    key=len, reverse=True)
PROV_RE = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, PROV_NAMES)) + r")(?!\w)")
# Cơ quan cấp tỉnh nhưng tên KHÔNG nêu tỉnh (thường gặp trong infobox: "Giám đốc Sở Giáo dục và Đào tạo")
GENERIC_LOCAL = re.compile(r"^(?:Sở .+|Ban .+ (?:Tỉnh ủy|Thành ủy)|Ủy ban Kiểm tra (?:Tỉnh ủy|Thành ủy)|"
                           r"Văn phòng (?:Tỉnh ủy|Thành ủy|Ủy ban nhân dân)|Tỉnh ủy|Thành ủy|"
                           r"Công an (?:tỉnh|thành phố|cấp tỉnh)|Bộ Chỉ huy Quân sự(?: tỉnh| thành phố)?|"
                           r"Đoàn đại biểu Quốc hội(?: tỉnh| thành phố)?)$")


def prov_of_org(o: dict) -> str:
    """Tỉnh của cơ quan: ưu tiên tên tỉnh ghi trong tên (đúng thời điểm, kể cả tỉnh cũ trước sáp nhập)."""
    m = PROV_RE.search(o.get("name", ""))
    p = m.group(1) if m else (o.get("province") or "")
    return PROV_ALIAS.get(p, p)


def year(d: str) -> int | None:
    return int(d[:4]) if d and d[:4].isdigit() else None


def is_generic_local(o: dict) -> bool:
    return bool(GENERIC_LOCAL.match(o["name"])) and not PROV_RE.search(o["name"])


def specific_name(generic: str, prov: str) -> str:
    """'Sở Y tế' + 'Nghệ An' -> 'Sở Y tế tỉnh Nghệ An';  'Ban Tổ chức Thành ủy' + 'Hà Nội' -> 'Ban Tổ chức Thành ủy Hà Nội'."""
    central = prov in CENTRAL
    pname = "Hồ Chí Minh" if prov == "Thành phố Hồ Chí Minh" else prov
    if re.search(r"(?:Tỉnh ủy|Thành ủy)$", generic):
        unit = "Thành ủy" if central else "Tỉnh ủy"
        return re.sub(r"(?:Tỉnh ủy|Thành ủy)$", unit, generic) + " " + (prov if prov != "Thành phố Hồ Chí Minh" else prov)
    base = re.sub(r"\s+(?:tỉnh|thành phố|cấp tỉnh)$", "", generic)
    return f"{base} {'thành phố' if central else 'tỉnh'} {pname}"


# ------------------------------------------------------------------ 2. chức danh
EXTRA_TITLES = ["Tư lệnh", "Phó Tư lệnh", "Chính ủy", "Phó Chính ủy", "Tổng Tham mưu trưởng", "Phó Tổng Tham mưu trưởng",
                "Đại sứ", "Chủ nhiệm", "Phó Chủ nhiệm", "Bí thư thứ nhất", "Thủ trưởng", "Trợ lý", "Thư ký",
                "Phó Chủ tịch Thường trực", "Phó Bí thư Thường trực", "Phó Trưởng ban Thường trực", "Thứ trưởng Thường trực"]
TITLES = sorted(set(ALL_TITLES) | set(EXTRA_TITLES), key=len, reverse=True)
ORG_START = re.compile(r"^(?:Bộ|Ủy ban|Ban|Tỉnh ủy|Thành ủy|Huyện ủy|Hội đồng|Văn phòng|Cục|Tổng cục|Vụ|Quốc hội|Chính phủ|"
                       r"Tòa|Viện|Sở|Đảng|Học viện|Đại học|Ngân hàng|Tập đoàn|Tổng công ty|Kiểm toán|Thanh tra|Quân|Bộ đội|"
                       r"Công an|Đoàn|Trung ương|UBND|HĐND|Mặt trận|Liên|Hội|Thông tấn|Đài|Báo|Kho bạc|Bảo hiểm|Nhà nước|"
                       r"nước|tỉnh|thành phố|huyện|Tổng)\b")


SPECIAL = {  # (org_id, chức danh) -> chức danh chuẩn
    ("org:ban_bi_thu", "Bí thư"): "Bí thư Trung ương Đảng",
    ("org:ban_bi_thu", "Thường trực"): "Thường trực Ban Bí thư",
    ("org:chu_tich_nuoc", "Chủ tịch"): "Chủ tịch nước",
    ("org:quoc_hoi", "Đại biểu"): "Đại biểu Quốc hội",
    ("org:bo_chinh_tri", "Ủy viên"): "Ủy viên Bộ Chính trị",
    ("org:chu_tich_nuoc", "Phó Chủ tịch"): "Phó Chủ tịch nước",
    ("org:ban_chap_hanh_trung_uong_dang", "Ủy viên"): "Ủy viên Trung ương Đảng",
    ("org:ban_chap_hanh_trung_uong_dang", "Ủy viên Ban Chấp hành Trung ương Đảng"): "Ủy viên Trung ương Đảng",
    ("org:ban_chap_hanh_trung_uong_dang", "Ủy viên dự khuyết"): "Ủy viên dự khuyết Trung ương Đảng",
}


def norm_role(role: str, org_name: str = "", org_id: str = "") -> tuple[str, str]:
    """-> (chức danh chuẩn, tiền tố trạng thái: '', 'nguyên', 'tân', 'quyền')."""
    r = norm_text(role or "").strip(" ,;")
    pre = ""
    m = re.match(r"^(nguyên|tân|cựu|cố|quyền)\s+", r, re.I)
    if m:
        pre = {"cựu": "nguyên", "cố": "nguyên"}.get(m.group(1).lower(), m.group(1).lower())
        r = r[m.end():]
    # bỏ phần tên cơ quan trùng với cơ quan của cạnh ("Ủy viên Bộ Chính trị" @ Bộ Chính trị -> "Ủy viên")
    for on in {norm_text(org_name), re.sub(r" Việt Nam$", "", norm_text(org_name))} - {""}:
        i = r.lower().find(" " + on.lower())
        if i > 0 and i + 1 + len(on) >= len(r) - 12:
            r = r[:i].strip(" ,")
            break
    r = re.sub(r"\bTrưởng Ban\b", "Trưởng ban", r)
    r = re.sub(r"\b([Tt])hường trực\b", "Thường trực", r)
    r = re.sub(r"^Phó (\w)", lambda x: "Phó " + x.group(1).upper(), r)
    r = re.sub(r"^Phó Trưởng Ban\b", "Phó Trưởng ban", r)
    for t in TITLES:  # cắt phần tên cơ quan dính sau chức danh
        tl = re.sub(r"\bTrưởng Ban\b", "Trưởng ban", t)
        if r.lower().startswith(tl.lower()) and len(r) > len(tl):
            rest = r[len(tl):].strip(" ,")
            if ORG_START.match(rest) and t not in ("Ủy viên", "Bí thư", "Trưởng", "Phó Trưởng") or not rest:
                r = tl
            break
    if r == "Phó":
        r = "Cấp phó"
    r = (r[:1].upper() + r[1:]) if r else ""
    return SPECIAL.get((org_id, r), r), pre


def role_kind(r: str) -> str:
    if r.startswith(("Ủy viên", "Đại biểu", "Thành viên")):
        return "Thành viên"
    if r.startswith("Phó") or r.startswith("Cấp phó") or " phó" in r.lower():
        return "Cấp phó"
    return "Cấp trưởng"


def short_org(name: str) -> str:
    return (name.replace("Ủy ban nhân dân", "UBND").replace("Hội đồng nhân dân", "HĐND")
            .replace("Ủy ban Mặt trận Tổ quốc Việt Nam", "UBMTTQ").replace("Ban Chấp hành Trung ương Đảng", "BCH Trung ương Đảng"))


def main(news_first: bool = False):
    OUT.mkdir(parents=True, exist_ok=True)
    persons = {r["id"]: r for f in ("nodes_person.csv", "nodes_person_news.csv") for r in read(f)}
    orgs = {r["id"]: r for f in ("nodes_org.csv", "nodes_org_news.csv") for r in read(f)}
    provs = {r["id"]: r for f in ("nodes_province.csv", "nodes_province_news.csv") for r in read(f)}
    edges = read("edges_wiki.csv") + read("edges_news.csv") + read("edges_family.csv")
    for edge in edges:
        if edge["rel"] == "QUE_QUAN" and edge.get("source") == "wikipedia:nơi sinh":
            edge["rel"] = "NOI_SINH"
    bad_pids = {pid for pid, p in persons.items()
                if p.get("name") in HISTORICAL_OR_FOREIGN or pid == "per:news:ho_chi_minh"}
    persons = {pid: p for pid, p in persons.items() if pid not in bad_pids}
    edges = [e for e in edges if e["src"] not in bad_pids and e["dst"] not in bad_pids]
    if news_first:
        mentioned = {r["person_id"] for r in read("person_mentions_news.csv") if r["person_id"] not in bad_pids}
        if not mentioned:
            raise RuntimeError("news-first requires person_mentions_news.csv with recognized people")
        persons = {pid: p for pid, p in persons.items() if pid in mentioned}
        edges = [e for e in edges if
                 (e["src_label"] != "Person" or e["src"] in persons) and
                 (e["dst_label"] != "Person" or e["dst"] in persons)]
    print(f"vào: {len(persons)} người, {len(orgs)} cơ quan, {len(provs)} tỉnh, {len(edges)} cạnh")

    # ---- 1. gộp cơ quan
    deg = Counter()
    for e in edges:
        deg[e["src"]] += 1; deg[e["dst"]] += 1
    groups = defaultdict(list)
    for oid, o in orgs.items():
        groups[org_key(o["name"])].append(oid)
    remap, dropped = {}, set()
    for key, ids in groups.items():
        if key in GENERIC_ORG_KEYS:
            dropped.update(ids)
            continue
        keep = max(ids, key=lambda i: (deg[i], -len(i)))
        names = [orgs[i]["name"] for i in ids]
        abbr = lambda n: bool(re.search(r"(?<!\w)(?:Tp|TP|UBND|HĐND)\.?(?!\w)| - ", n))  # noqa: E731
        long_ = any(n.startswith(KEEP_LONG) for n in names)
        name = min(names, key=lambda n: (abbr(n), -len(n) if long_ else len(n)))  # ưu tiên tên viết đầy đủ
        orgs[keep]["name"] = name
        for i in ids:
            if i != keep:
                remap[i] = keep
                for k in ("type", "level", "province"):
                    if not orgs[keep].get(k) or orgs[keep].get(k) == "Khác":
                        orgs[keep][k] = orgs[i].get(k) or orgs[keep].get(k)
    for i in list(remap) + list(dropped):
        orgs.pop(i, None)
    print(f"gộp {len(remap)} cơ quan trùng, bỏ {len(dropped)} cơ quan chung chung")

    def fix(e):
        e = dict(e)
        e["src"] = remap.get(e["src"], e["src"]); e["dst"] = remap.get(e["dst"], e["dst"])
        if e.get("to_org"):
            e["to_org"] = remap.get(e["to_org"], e["to_org"])
        return e

    edges = [fix(e) for e in edges if e["src"] not in dropped and e["dst"] not in dropped]
    edges = [e for e in edges if e["src"] != e["dst"]]

    out_edges = []

    # ---- 1c. cụ thể hoá cơ quan cấp tỉnh không nêu tên tỉnh, dựa vào tỉnh nơi người đó công tác cùng thời kỳ
    key2org = {org_key(o["name"]): i for i, o in orgs.items()}
    prov_id = {}
    for pid_, pr in provs.items():
        if pr["name"] not in prov_id or pr.get("status") == "hiện hành":
            prov_id[pr["name"]] = pid_
    by_person = defaultdict(list)
    for e in edges:
        if e["rel"] == "GIU_CHUC_VU" and e["dst"] in orgs:
            by_person[e["src"]].append(e)
    n_gen = n_fixed = n_new = 0
    for e in edges:
        if e["rel"] != "GIU_CHUC_VU" or e["dst"] not in orgs or not is_generic_local(orgs[e["dst"]]):
            continue
        n_gen += 1
        s0, e0 = e.get("start") or "", e.get("end") or "9999"
        others = [(f, prov_of_org(orgs[f["dst"]])) for f in by_person[e["src"]]
                  if f is not e and not is_generic_local(orgs[f["dst"]])]
        others = [(f, p) for f, p in others if p]
        # (1) chức vụ cấp tỉnh cùng thời kỳ
        cands = {p for f, p in others
                 if not s0 or not f.get("start") or f["start"] <= s0 <= (f.get("end") or "9999") or s0 <= f["start"] <= e0}
        if len(cands) != 1:
            allp = {p for _, p in others}
            if len(allp) == 1:          # (2) cả sự nghiệp cấp tỉnh chỉ ở một tỉnh
                cands = allp
            else:                       # (3) chức vụ gần nhất về thời gian, cách <= 3 năm
                y0, y1 = year(s0), year(e.get("end") or "") or year(s0)
                best = None
                for f, p in others:
                    fs, fe = year(f.get("start") or ""), year(f.get("end") or "") or year(f.get("start") or "")
                    if None in (y0, y1, fs, fe):
                        continue
                    gap = max(0, fs - y1, y0 - fe)
                    if gap <= 3 and (best is None or gap < best[0]):
                        best = (gap, p)
                cands = {best[1]} if best else set()
        if len(cands) != 1:
            continue
        prov = cands.pop()
        name = specific_name(orgs[e["dst"]]["name"], prov)
        oid = key2org.get(org_key(name))
        if oid is None:
            oid = "org:" + slug(name)
            g = orgs[e["dst"]]
            orgs[oid] = {"id": oid, "name": name, "type": g.get("type") or "Cơ quan cấp tỉnh", "level": "Tỉnh",
                         "province": prov}
            key2org[org_key(name)] = oid
            if prov in prov_id:
                edges.append({"src": oid, "src_label": "Organization", "rel": "THUOC_DIA_PHUONG", "dst": prov_id[prov],
                              "dst_label": "Province", "source": "rule:cu_the_hoa_co_quan", "confidence": 0.9})
            n_new += 1
        e["dst"] = oid
        n_fixed += 1
    for o in orgs.values():
        o["cu_the"] = "False" if is_generic_local(o) else "True"
    print(f"cơ quan không nêu tỉnh: {n_gen} cạnh giữ chức -> cụ thể hoá {n_fixed} (tạo mới {n_new} cơ quan), "
          f"còn {n_gen - n_fixed} ghi '(chưa rõ tỉnh)'")

    # ---- 2+3. chức vụ
    positions = {}
    giu = defaultdict(list)  # (pid, posid) -> các bản ghi
    for e in edges:
        if e["rel"] != "GIU_CHUC_VU" or e["dst"] not in orgs:
            continue
        role, pre = norm_role(e.get("role", ""), orgs[e["dst"]]["name"], e["dst"])
        if not role:
            role = "Thành viên"
        o = orgs[e["dst"]]
        pos_id = "pos:" + slug(role) + "__" + e["dst"][4:]
        if pos_id not in positions:
            so = short_org(o["name"]) + (" (chưa rõ tỉnh)" if o.get("cu_the") == "False" else "")
            positions[pos_id] = {"id": pos_id, "name": role, "org_id": e["dst"], "org_name": o["name"],
                                 "hien_thi": role if so.lower() in role.lower() or role in SPECIAL.values() else f"{role} · {so}",
                                 "kind": role_kind(role), "level": o.get("level", "")}
        giu[(e["src"], pos_id)].append({**e, "_pre": pre})
    for pos_id, p in positions.items():
        out_edges.append({"src": pos_id, "src_label": "ChucVu", "rel": "THUOC_CO_QUAN", "dst": p["org_id"],
                          "dst_label": "Organization", "source": "rule:mo_hinh_chuc_vu", "confidence": 1.0})

    n_giu_in = sum(len(v) for v in giu.values())
    for (pid, pos_id), recs in giu.items():
        wiki = [r for r in recs if (r.get("source") or "").startswith("wikipedia")]
        news = [r for r in recs if r not in wiki]
        terms = {}
        for r in wiki:  # nhiệm kỳ theo năm bắt đầu
            k = (r.get("start") or "")[:4]
            t = terms.setdefault(k, dict(r))
            if r.get("start") and (not t.get("start") or r["start"] < t["start"]):
                t["start"] = r["start"]
            if r.get("end") and (not t.get("end") or r["end"] > t["end"]):
                t["end"] = r["end"]
            if r.get("current") == "True":
                t["current"] = "True"
        nw = sum(int(float(r.get("weight") or 1)) for r in news)
        if news:
            first = min(news, key=lambda r: r.get("start") or "9999")
            last = max(news, key=lambda r: r.get("date") or "")
            news_info = {"weight_tin_tuc": nw, "evidence": first.get("evidence", ""), "source_tin_tuc": first.get("source", ""),
                         "date": last.get("date", "")}
        if not terms:  # chỉ có trong tin tức
            former = all(r["_pre"] == "nguyên" for r in news)
            terms[""] = {"start": first.get("start", ""), "end": "", "current": str(not former),
                         "source": first.get("source", ""), "confidence": max(float(r.get("confidence") or 0.9) for r in news),
                         "method": "rule:appositive", **news_info}
        elif news:  # bổ sung bằng chứng tin tức vào nhiệm kỳ gần nhất của Wikipedia
            latest = max(terms, key=lambda k: k)
            terms[latest].update(news_info)
        for t in terms.values():
            out_edges.append({"src": pid, "src_label": "Person", "rel": "GIU_CHUC_VU", "dst": pos_id, "dst_label": "ChucVu",
                              "role": positions[pos_id]["name"], "start": t.get("start", ""), "end": t.get("end", ""),
                              "current": t.get("current", ""), "source": t.get("source", ""),
                              "confidence": t.get("confidence", 1.0), "weight": t.get("weight_tin_tuc", ""),
                              "evidence": t.get("evidence", ""), "date": t.get("date", ""),
                              "method": t.get("method", "") or "wikipedia:infobox",
                              "source_tin_tuc": t.get("source_tin_tuc", "")})
    n_giu_out = sum(1 for e in out_edges if e["rel"] == "GIU_CHUC_VU")

    # ---- 4. quan hệ người – người
    pp = defaultdict(list)
    for e in edges:
        if e["rel"] in ("KE_NHIEM", "LANH_DAO_TRUC_TIEP", "CAP_PHO"):
            pp[(e["src"], e["rel"], e["dst"])].append(e)
    merged = {}
    for (s, rel, d), recs in pp.items():
        roles = []
        for r in recs:
            ro = norm_text(r.get("role") or "")
            ro = re.sub(r"\bTrưởng Ban\b", "Trưởng ban", ro)
            if ro and ro not in roles and not any(ro in x for x in roles):
                roles = [x for x in roles if x not in ro] + [ro]
        starts = sorted(r["start"] for r in recs if r.get("start"))
        merged[(s, rel, d)] = {"src": s, "src_label": "Person", "rel": rel, "dst": d, "dst_label": "Person",
                               "role": "; ".join(roles[:3]), "start": starts[0] if starts else "",
                               "source": "; ".join(sorted({r["source"] for r in recs if r.get("source")}))[:300],
                               "confidence": 1.0, "weight": len(recs)}
    conflicts = 0
    for (s, rel, d), e in list(merged.items()):
        if rel != "KE_NHIEM" or (d, rel, s) not in merged or (s, rel, d) not in merged:
            continue
        o = merged[(d, rel, s)]
        if e["start"] and o["start"] and e["start"] != o["start"]:
            loser = (s, rel, d) if e["start"] < o["start"] else (d, rel, s)  # người kế nhiệm nhậm chức muộn hơn
            merged.pop(loser); conflicts += 1
    out_edges += list(merged.values())
    n_pp_in = sum(len(v) for v in pp.values())

    # ---- cạnh còn lại
    rest = {}
    for e in edges:
        if e["rel"] in ("GIU_CHUC_VU", "KE_NHIEM", "LANH_DAO_TRUC_TIEP", "CAP_PHO"):
            continue
        # News assertions have their own identity; identical endpoint pairs can
        # represent separate decisions on separate dates or in separate reports.
        k = (e["src"], e["rel"], e["dst"], e.get("event_id") or "")
        a = rest.get(k)
        if a is None:
            rest[k] = dict(e)
            continue
        a["weight"] = int(float(a.get("weight") or 1)) + int(float(e.get("weight") or 1))
        if e.get("start") and (not a.get("start") or e["start"] < a["start"]):
            a["start"] = e["start"]
        if (e.get("date") or "") > (a.get("date") or ""):
            a["date"] = e["date"]
        a["confidence"] = max(float(a.get("confidence") or 0), float(e.get("confidence") or 0))
    out_edges += list(rest.values())

    # ---- kiểm tra đầu mút & ghi
    ids = set(persons) | set(orgs) | set(provs) | set(positions)
    bad = [e for e in out_edges if e["src"] not in ids or e["dst"] not in ids]
    out_edges = [e for e in out_edges if e["src"] in ids and e["dst"] in ids]
    used = {e["src"] for e in out_edges} | {e["dst"] for e in out_edges}
    orgs_out = [o for i, o in orgs.items() if i in used or not i.startswith("org:")]

    mention_counts = Counter(r["person_id"] for r in read("person_mentions_news.csv"))

    # Xác định trạng thái cán bộ: "đương nhiệm" / "đã về hưu" / "chưa rõ"
    for pid, p in persons.items():
        if p.get("wiki_title") and p.get("hometown"):
            p["birth_place"] = p["hometown"]
            p["hometown"] = ""
        p["news_article_count"] = mention_counts.get(pid, 0)
        p["verification_status"] = ("needs_review" if pid not in used else "linked")
        person_pos = [e for e in out_edges if e["src"] == pid and e["rel"] == "GIU_CHUC_VU"]
        if not person_pos:
            p["status"] = p.get("status") or "chưa rõ"
        elif any(e.get("current") in (True, "True") for e in person_pos):
            p["status"] = "đương nhiệm"
        else:
            p["status"] = "chưa rõ"

    write("nodes_person.csv", list(persons.values()),
          ["id", "name", "wiki_title", "wikidata", "birth_year", "hometown", "birth_place", "status", "source",
           "news_article_count", "verification_status"])
    write("nodes_org.csv", orgs_out, ["id", "name", "type", "level", "province", "cu_the"])
    write("nodes_position.csv", list(positions.values()), ["id", "name", "org_id", "org_name", "hien_thi", "kind", "level"])
    write("nodes_province.csv", list(provs.values()), ["id", "name", "status", "valid_from"])
    fields = ["src", "src_label", "rel", "dst", "dst_label", "role", "start", "end", "current", "source", "confidence",
              "weight", "evidence", "date", "method", "to_org", "source_tin_tuc", "event_id", "event_date",
              "review_status"]
    write("edges.csv", out_edges, fields)

    c = Counter(e["rel"] for e in out_edges)
    print(f"GIU_CHUC_VU: {n_giu_in} bản ghi -> {n_giu_out} cạnh tới {len(positions)} nút chức vụ")
    print(f"quan hệ người–người: {n_pp_in} bản ghi -> {len(merged)} cạnh (bỏ {conflicts} cạnh kế nhiệm ngược chiều)")
    print(f"bỏ {len(bad)} cạnh có đầu mút không tồn tại")
    print(f"ra: {len(persons)} người, {len(orgs_out)} cơ quan, {len(positions)} chức vụ, {len(provs)} tỉnh, "
          f"{len(out_edges)} cạnh, {len(c)} loại")
    for k, v in c.most_common():
        print(f"  {k:20s} {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--news-first", action="store_true", help="Only include people recognized in news articles")
    main(news_first=parser.parse_args().news_first)
