"""Bước 4 – Chuẩn hoá thực thể & sinh nút/cạnh "khung" từ Wikipedia.

Đầu vào : data/interim/persons_raw.jsonl, data/interim/redirects.json, config/*.json
Đầu ra  : data/processed/
            nodes_person.csv, nodes_org.csv, nodes_province.csv
            edges_wiki.csv                (cạnh có cấu trúc, độ tin cậy cao)
            gazetteer_person.json         (tên/biến thể -> id; dùng cho NER tin tức)
            gazetteer_org.json            (tên/alias -> id cơ quan)
          data/interim/expand_titles.json (trang người được liên kết nhưng chưa tải -> vòng mở rộng)

Loại cạnh sinh ở bước này:
  GIU_CHUC_VU        Person -> Org        (role, start, end, current)
  KE_NHIEM           Person -> Person     (người kế nhiệm -> người tiền nhiệm, theo chức vụ)
  LANH_DAO_TRUC_TIEP Person -> Person     (cấp trên trực tiếp -> cấp dưới, theo infobox)
  CAP_PHO            Person -> Person     (cấp phó -> người đứng đầu)
  TRUC_THUOC         Org -> Org           (cơ cấu tổ chức, suy từ tên)
  THUOC_DIA_PHUONG   Org -> Province
  HOP_NHAT_VAO       Org -> Org / Province -> Province (sắp xếp bộ máy 2025)
  QUE_QUAN           Person -> Province
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
PROC = ROOT / "data" / "processed"
CFG = ROOT / "config"

MIN_YEAR = 2006  # chỉ giữ chức vụ còn hiệu lực từ năm này trở đi (giai đoạn hiện đại)


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").strip()


def slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s.replace("Đ", "D").replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# ---------------------------------------------------------------- tỉnh / thành
prov_cfg = json.loads((CFG / "provinces_2025.json").read_text(encoding="utf-8"))
OLD_TO_NEW: dict[str, str] = {}
for new, olds in prov_cfg["merge"].items():
    for o in olds:
        OLD_TO_NEW[o] = new
PROV_ALIASES = {**{k: v for k, v in prov_cfg["aliases"].items()},
                "Thành phố Hồ Chí Minh": "Thành phố Hồ Chí Minh", "Hồ Chí Minh": "Thành phố Hồ Chí Minh",
                "Huế": "Thừa Thiên Huế"}
ALL_PROV_NAMES = sorted(set(OLD_TO_NEW) | set(PROV_ALIASES), key=len, reverse=True)
PROV_RE = re.compile(r"(?<![\wÀ-ỹ])(" + "|".join(map(re.escape, ALL_PROV_NAMES)) + r")(?![\wÀ-ỹ])")


def find_province(text: str) -> str | None:
    """Tên tỉnh (đơn vị cũ, trước 2025) xuất hiện trong chuỗi."""
    m = PROV_RE.search(text or "")
    if not m:
        return None
    p = m.group(1)
    return PROV_ALIASES.get(p, p)


# ---------------------------------------------------------------- cơ quan
org_cfg = json.loads((CFG / "org_mergers_2025.json").read_text(encoding="utf-8"))
ORG_ALIASES = {nfc(k): nfc(v) for k, v in org_cfg["aliases"].items()}
ORG_ALIASES.update({
    "Trung ương Đảng": "Ban Chấp hành Trung ương Đảng",
    "Ban Chấp hành Trung ương": "Ban Chấp hành Trung ương Đảng",
    "Ban Chấp hành Trung ương Đảng Cộng sản Việt Nam": "Ban Chấp hành Trung ương Đảng",
    "Ban Bí thư Trung ương Đảng": "Ban Bí thư",
    "Ban Bí thư Ban Chấp hành Trung ương Đảng": "Ban Bí thư",
    "Ủy ban Kiểm tra Trung ương Đảng": "Ủy ban Kiểm tra Trung ương",
    "Chính phủ Việt Nam": "Chính phủ",
    "Quốc hội Việt Nam": "Quốc hội",
    "Quốc hội nước": "Quốc hội",
    "Chính phủ nước": "Chính phủ",
    "Quốc hội Việt Nam khóa XVI": "Quốc hội",
    "Văn phòng Quốc hội Việt Nam": "Văn phòng Quốc hội",
    "Thành đoàn TPHCM": "Thành đoàn Thành phố Hồ Chí Minh",
    "Ngân hàng Nhà nước": "Ngân hàng Nhà nước Việt Nam",
    "Thanh tra Chính phủ Việt Nam": "Thanh tra Chính phủ",
    "Kiểm toán Nhà nước Việt Nam": "Kiểm toán Nhà nước",
    "Mặt trận Tổ quốc Việt Nam": "Ủy ban Trung ương Mặt trận Tổ quốc Việt Nam",
})
MERGERS = [(nfc(m["old"]), nfc(m["new"]), m["date"]) for m in org_cfg["mergers"]]

ORG_PREFIX = re.compile(
    r"^(Bộ|Ban|Ủy ban|Văn phòng|Thành ủy|Tỉnh ủy|Đảng ủy|Đảng đoàn|Ban cán sự|Hội đồng|Tập đoàn|Tổng công ty|Công ty|"
    r"Ngân hàng|Chính phủ|Quốc hội|Kiểm toán|Thanh tra|Tòa án|Viện|Học viện|Đại học|Trường|Tổng cục|Cục|Vụ|"
    r"Báo|Đài|Thông tấn|Tạp chí|Quân khu|Quân chủng|Quân đoàn|Binh chủng|Bộ đội|Bộ Tư lệnh|Công an|"
    r"Tổng Liên đoàn|Liên đoàn|Liên hiệp|Hội|Trung ương Đoàn|Đoàn|Tỉnh đoàn|Thành đoàn|Mặt trận|Sở|Kho bạc|Bảo hiểm|"
    r"Đại sứ quán|Huyện ủy|Thị ủy|Quận ủy|Trung tâm|Quân đội|Ủy ban|Tổng cục|Bộ Chỉ huy|Bộ Tổng Tham mưu)\b")
# chuỗi bắt đầu bằng các từ này là chức danh lọt vào, không phải cơ quan
ROLE_LEAK = re.compile(r"^(Quyền|Phụ trách|Thư ký|Tổng Thư ký|Trưởng đoàn|Tham mưu trưởng|Chỉ huy trưởng|Thủ trưởng|"
                       r"Đặc mệnh|thứ nhất|Thường trực|Ủy viên|Trợ lý|Người phát ngôn)\b", re.I)
GENERIC_LINKS = {"Ủy ban nhân dân", "Hội đồng nhân dân", "Tỉnh ủy", "Thành ủy", "Bộ trưởng", "Thứ trưởng",
                 "Đại biểu Quốc hội", "Việt Nam", "Ủy ban", "Đoàn ĐBQH", "Ban Cán sự Đảng", "Công an nhân dân"}

ORG_TYPES = [  # (regex, loại, cấp)
    (r"^Ban Chấp hành Trung ương Đảng$|^Bộ Chính trị$|^Ban Bí thư$|^Quân ủy Trung ương$", "Cơ quan lãnh đạo Đảng", "TW"),
    (r"^(Ban|Ủy ban Kiểm tra|Văn phòng) .*Trung ương", "Cơ quan Đảng TW", "TW"),
    (r"^Chính phủ$|^Chủ tịch nước$|^Văn phòng Chủ tịch nước$", "Thiết chế nhà nước", "TW"),
    (r"^Quốc hội$|^Ủy ban Thường vụ Quốc hội$|^Văn phòng Quốc hội$|^Hội đồng Dân tộc$", "Quốc hội", "TW"),
    (r"^Ủy ban .*(Quốc hội)?$(?<!nhân dân)", "Cơ quan Quốc hội", "TW"),
    (r"^Bộ ", "Bộ", "TW"),
    (r"^(Ngân hàng Nhà nước Việt Nam|Thanh tra Chính phủ|Văn phòng Chính phủ|Ủy ban Dân tộc)$", "Cơ quan ngang bộ", "TW"),
    (r"^(Kiểm toán Nhà nước|Tòa án nhân dân tối cao|Viện kiểm sát nhân dân tối cao)$", "Cơ quan tư pháp/kiểm toán", "TW"),
    (r"^(Tập đoàn|Tổng công ty|Ngân hàng)", "Doanh nghiệp nhà nước", "TW"),
    (r"^Ban Chỉ đạo", "Ban Chỉ đạo", ""),
    (r"^(Tỉnh ủy|Thành ủy)", "Cấp ủy tỉnh", "Tỉnh"),
    (r"^(Huyện ủy|Thị ủy|Quận ủy)", "Cấp ủy huyện (bỏ cấp huyện từ 7/2025)", "Huyện"),
    (r"^Đảng ủy", "Đảng ủy", ""),
    (r"^Ban .*(Tỉnh ủy|Thành ủy)", "Cơ quan Đảng tỉnh", "Tỉnh"),
    (r"^(Tòa án|Viện kiểm sát)", "Cơ quan tư pháp", ""),
    (r"^(Tỉnh đoàn|Thành đoàn|Liên đoàn|Liên hiệp|Mặt trận|Ủy ban Mặt trận)", "Mặt trận & đoàn thể", ""),
    (r"^Ủy ban nhân dân", "UBND tỉnh", "Tỉnh"),
    (r"^Hội đồng nhân dân", "HĐND tỉnh", "Tỉnh"),
    (r"^Đoàn đại biểu Quốc hội", "Đoàn ĐBQH tỉnh", "Tỉnh"),
    (r"^Sở ", "Sở", "Tỉnh"),
    (r"^Công an (tỉnh|thành phố)", "Công an tỉnh", "Tỉnh"),
    (r"^(Quân khu|Quân chủng|Quân đoàn|Binh chủng|Bộ Tư lệnh|Tổng cục|Bộ Tổng Tham mưu)", "Lực lượng vũ trang", "TW"),
    (r"^(Tổng cục|Cục|Vụ) ", "Đơn vị thuộc bộ", "TW"),
    (r"^(Học viện|Đại học|Trường|Viện)", "Đơn vị sự nghiệp", "TW"),
    (r"^(Báo|Đài|Thông tấn|Tạp chí)", "Cơ quan báo chí", "TW"),
    (r"^(Ủy ban Trung ương Mặt trận|Tổng Liên đoàn|Trung ương Đoàn|Trung ương Hội|Hội )", "Mặt trận & đoàn thể", "TW"),
]


def org_type(name: str) -> tuple[str, str]:
    for rx, t, lvl in ORG_TYPES:
        if re.search(rx, name):
            return t, lvl
    return "Khác", ""


def clean_org(s: str) -> str:
    s = nfc(s)
    s = re.sub(r"\s*\((Việt Nam|nước|tỉnh|thành phố)\)", "", s)
    s = re.sub(r"\s+(Đảng Cộng sản Việt Nam|Đảng Cộng sản)$", "", s)
    s = re.sub(r"\s*\(.*?\)\s*$", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ,.-–")
    s = s.replace("Uỷ", "Ủy").replace("uỷ", "ủy").replace("Hoá", "Hóa").replace("hoá", "hóa")
    s = re.sub(r"^(UBND|Ủy ban Nhân dân)\b", "Ủy ban nhân dân", s)
    s = re.sub(r"^(HĐND|Hội đồng Nhân dân)\b", "Hội đồng nhân dân", s)
    s = re.sub(r"^(Ủy ban nhân dân|Hội đồng nhân dân) (Tỉnh|Thành phố|TP\.?)\s", lambda m: f"{m.group(1)} {'tỉnh' if m.group(2) == 'Tỉnh' else 'thành phố'} ", s)
    return ORG_ALIASES.get(s, s)


def canon_org(role: str, org: str, link: str | None) -> str | None:
    role = role or ""
    org = clean_org(org)
    link_c = clean_org(link) if link else ""
    if role == "Đại biểu Quốc hội":
        return "Quốc hội"
    if role in ("Thủ tướng", "Phó Thủ tướng", "Phó Thủ tướng Thường trực") and not ORG_PREFIX.match(org):
        return "Chính phủ"
    if role in ("Chủ tịch nước", "Phó Chủ tịch nước"):
        return "Chủ tịch nước"
    if role in ("Tổng Bí thư",):
        return "Ban Chấp hành Trung ương Đảng"
    if role == "Thường trực Ban Bí thư":
        return "Ban Bí thư"
    if role == "Bí thư" and org in ("Ban Chấp hành Trung ương Đảng", "Trung ương Đảng"):
        return "Ban Bí thư"
    org = re.sub(r"^(Quyền|Phụ trách)\s+", "", org)
    if not ORG_PREFIX.match(org):
        if link_c and ORG_PREFIX.match(link_c) and link_c not in GENERIC_LINKS:
            org = link_c
        elif re.match(r"^(Chỉ đạo|Tuyên giáo|Tổ chức|Nội chính|Kinh tế|Dân vận|Đối ngoại|Chính sách|Tài chính Quản trị)", org) \
                or (role.endswith("Trưởng ban") and org):
            org = clean_org("Ban " + org)
        elif re.match(r"^(Chính trị|Hậu cần|Kỹ thuật|Cảnh sát|An ninh)\s", org):
            org = clean_org("Cục " + org) if "Quân khu" in org or "Bộ" in org else org
    org = clean_org(org)
    # chỉ nhận chuỗi bắt đầu bằng tiền tố tổ chức hợp lệ, không bắt đầu bằng chữ thường / chức danh
    if (not org or len(org) < 4 or org in GENERIC_LINKS or org[0].islower()
            or ROLE_LEAK.match(org) or not ORG_PREFIX.match(org)):
        return None
    return ORG_ALIASES.get(org, org)


def year_of(d: str | None) -> int | None:
    return int(d[:4]) if d and d[:4].isdigit() else None


# ---------------------------------------------------------------- main
def main():
    redirects = json.loads((INTERIM / "redirects.json").read_text(encoding="utf-8")) \
        if (INTERIM / "redirects.json").exists() else {}
    resolve = lambda t: redirects.get(t, t)  # noqa: E731

    people = [json.loads(l) for l in (INTERIM / "persons_raw.jsonl").open(encoding="utf-8")]
    by_title = {p["title"]: p for p in people}

    # -------- lọc theo giai đoạn: còn ít nhất 1 chức vụ từ MIN_YEAR, hoặc thuộc khóa gần đây
    def modern(p):
        for pos in p["positions"]:
            ys = [year_of(pos["start"]), year_of(pos["end"])]
            if pos["current"] or any(y and y >= MIN_YEAR for y in ys):
                return True
        cats = " ".join(p["wiki_categories"])
        return bool(re.search(r"khóa (X|XI|XII|XIII|XIV|XV|XVI)\b", cats))

    kept = {t: p for t, p in by_title.items() if modern(p)}
    print(f"Người có infobox: {len(by_title)} -> giữ giai đoạn hiện đại: {len(kept)}")

    # -------- chỉ mục tên -> danh sách người (để liên kết tên không có link)
    name_idx = defaultdict(set)
    for t, p in kept.items():
        name_idx[nfc(p["name"])].add(t)

    def person_ref(x: dict) -> str | None:
        if x.get("link"):
            t = resolve(x["link"])
            if t in kept:
                return t
            return None
        cands = name_idx.get(nfc(x["name"]), set())
        return next(iter(cands)) if len(cands) == 1 else None

    # -------- tập link người chưa tải -> vòng mở rộng
    expand = Counter()
    for p in kept.values():
        for pos in p["positions"]:
            for key in ("superiors", "deputies", "predecessors", "successors"):
                for x in pos[key]:
                    if x.get("link") and resolve(x["link"]) not in by_title:
                        expand[x["link"]] += 1
    (INTERIM / "expand_titles.json").write_text(json.dumps(sorted(expand), ensure_ascii=False), encoding="utf-8")

    # -------- nút & cạnh
    orgs: dict[str, dict] = {}
    provinces: dict[str, dict] = {}
    edges: list[dict] = []
    edge_keys = set()

    def add_prov(old_name: str) -> str:
        new = OLD_TO_NEW.get(old_name, old_name)
        pid_new = "prov:" + slug(new)
        provinces.setdefault(pid_new, {"id": pid_new, "name": new, "status": "hiện hành", "valid_from": "2025-07-01"})
        if old_name != new:
            pid_old = "prov:" + slug(old_name) + "_cu"
            provinces.setdefault(pid_old, {"id": pid_old, "name": old_name, "status": "đã sáp nhập", "valid_from": ""})
            add_edge(pid_old, "Province", "HOP_NHAT_VAO", pid_new, "Province", start="2025-07-01",
                     source="config/provinces_2025.json")
            return pid_old
        return pid_new

    def add_org(name: str) -> str:
        oid = "org:" + slug(name)
        if oid not in orgs:
            t, lvl = org_type(name)
            prov = find_province(name)
            orgs[oid] = {"id": oid, "name": name, "type": t, "level": lvl or ("Tỉnh" if prov else ""),
                         "province": OLD_TO_NEW.get(prov, prov) if prov else ""}
            if prov:
                add_edge(oid, "Organization", "THUOC_DIA_PHUONG", add_prov(prov), "Province",
                         source="rule:tên cơ quan")
        return oid

    def add_edge(src, sl, rel, dst, dl, **props):
        if src == dst:
            return
        key = (src, rel, dst, props.get("role", ""), props.get("start", ""))
        if key in edge_keys:
            return
        edge_keys.add(key)
        edges.append({"src": src, "src_label": sl, "rel": rel, "dst": dst, "dst_label": dl,
                      "role": props.get("role", ""), "start": props.get("start") or "",
                      "end": props.get("end") or "", "current": props.get("current", ""),
                      "source": props.get("source", "wikipedia"), "confidence": props.get("confidence", 1.0)})

    pid = lambda t: "per:" + slug(t)  # noqa: E731
    persons_rows = []
    for t, p in kept.items():
        hometown = find_province(p["birth_place"])
        persons_rows.append({"id": pid(t), "name": nfc(p["name"]), "wiki_title": t, "wikidata": p.get("wikidata") or "",
                             "birth_year": p.get("birth_year") or "", "hometown": hometown or ""})
        if hometown:
            add_edge(pid(t), "Person", "QUE_QUAN", add_prov(hometown), "Province", source="wikipedia:nơi sinh")
        for pos in p["positions"]:
            ys = [year_of(pos["start"]), year_of(pos["end"])]
            if not (pos["current"] or any(y and y >= MIN_YEAR for y in ys)):
                continue
            org = canon_org(pos["role"], pos["org"], pos["org_link"])
            role = pos["role"] or pos["title_raw"][:60]
            src = f"wikipedia:{t}"
            if org:
                add_edge(pid(t), "Person", "GIU_CHUC_VU", add_org(org), "Organization", role=role,
                         start=pos["start"], end=pos["end"], current=pos["current"], source=src)
            for x in pos["predecessors"]:
                r = person_ref(x)
                if r:
                    add_edge(pid(t), "Person", "KE_NHIEM", pid(r), "Person", role=f"{role} {org or ''}".strip(),
                             start=pos["start"], source=src)
            for x in pos["successors"]:
                r = person_ref(x)
                if r:
                    add_edge(pid(r), "Person", "KE_NHIEM", pid(t), "Person", role=f"{role} {org or ''}".strip(),
                             start=pos["end"], source=src)
            for x in pos["superiors"]:
                r = person_ref(x)
                if r:
                    add_edge(pid(r), "Person", "LANH_DAO_TRUC_TIEP", pid(t), "Person",
                             role=f"{pos['superior_role']} -> {role}".strip(" ->"), start=pos["start"],
                             end=pos["end"], current=pos["current"], source=src)
            for x in pos["deputies"]:
                r = person_ref(x)
                if r:
                    add_edge(pid(r), "Person", "CAP_PHO", pid(t), "Person", role=f"Cấp phó {role} {org or ''}".strip(),
                             start=pos["start"], end=pos["end"], source=src)

    # -------- TRUC_THUOC theo cơ cấu (suy từ tên) + HOP_NHAT_VAO
    names = {o["name"]: oid for oid, o in orgs.items()}
    def link_parent(child_name, parent_name, why):
        add_edge(names[child_name], "Organization", "TRUC_THUOC", add_org(parent_name), "Organization",
                 source=f"rule:{why}")
    for name in list(names):
        t, _ = org_type(name)
        if t == "Bộ" or t == "Cơ quan ngang bộ":
            link_parent(name, "Chính phủ", "bộ thuộc Chính phủ")
        elif t == "Cơ quan Đảng TW":
            link_parent(name, "Ban Chấp hành Trung ương Đảng", "cơ quan Đảng TW")
        elif t == "Cơ quan Quốc hội":
            link_parent(name, "Quốc hội", "cơ quan của Quốc hội")
        elif name in ("Bộ Chính trị", "Ban Bí thư"):
            link_parent(name, "Ban Chấp hành Trung ương Đảng", "cơ quan lãnh đạo Đảng")
        elif t == "UBND tỉnh":
            link_parent(name, "Chính phủ", "UBND tỉnh chịu sự lãnh đạo của Chính phủ")
    for old, new, date in MERGERS:
        add_edge(add_org(old), "Organization", "HOP_NHAT_VAO", add_org(new), "Organization", date=date,
                 start=date, source="config/org_mergers_2025.json")

    # -------- ghi file
    PROC.mkdir(parents=True, exist_ok=True)
    def write_csv(path, rows, fields):
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    write_csv(PROC / "nodes_person.csv", persons_rows, ["id", "name", "wiki_title", "wikidata", "birth_year", "hometown"])
    write_csv(PROC / "nodes_org.csv", list(orgs.values()), ["id", "name", "type", "level", "province"])
    write_csv(PROC / "nodes_province.csv", list(provinces.values()), ["id", "name", "status", "valid_from"])
    write_csv(PROC / "edges_wiki.csv", edges,
              ["src", "src_label", "rel", "dst", "dst_label", "role", "start", "end", "current", "source", "confidence"])

    # -------- gazetteer cho bước NER tin tức
    gaz_p = defaultdict(list)
    for r in persons_rows:
        gaz_p[r["name"]].append({"id": r["id"], "birth_year": r["birth_year"]})
    (PROC / "gazetteer_person.json").write_text(json.dumps(gaz_p, ensure_ascii=False, indent=0), encoding="utf-8")
    gaz_o = {o["name"]: oid for oid, o in orgs.items()}
    for alias, target in ORG_ALIASES.items():
        if target in gaz_o:
            gaz_o.setdefault(alias, gaz_o[target])
    (PROC / "gazetteer_org.json").write_text(json.dumps(gaz_o, ensure_ascii=False, indent=0), encoding="utf-8")

    print(f"Nút: {len(persons_rows)} người, {len(orgs)} cơ quan, {len(provinces)} tỉnh | Cạnh: {len(edges)}")
    for rel, n in Counter(e["rel"] for e in edges).most_common():
        print(f"   {rel:20s} {n}")
    print(f"Trang người cần mở rộng (liên kết chưa tải): {len(expand)}")


if __name__ == "__main__":
    main()
