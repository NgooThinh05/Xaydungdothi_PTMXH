"""Bước 1 – Duyệt cây thể loại Wikipedia tiếng Việt để lấy danh sách trang ứng viên.

Đầu ra: data/interim/wiki_candidates.json
  {title: {"kind": "person"|"org", "categories": [thể loại tìm thấy]}}

Cách làm: BFS từ các thể loại gốc, giới hạn độ sâu, loại các thể loại thuộc
chế độ/thời kỳ cũ (VNCH, Đế quốc, khóa I–IX ...) để mạng tập trung vào giai đoạn hiện đại.
"""
from __future__ import annotations

import json
import re
from collections import deque
from pathlib import Path

from wiki_client import category_members

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "wiki_candidates.json"

PERSON_ROOTS = {
    # Lãnh đạo Đảng
    "Thể loại:Ủy viên Ban Chấp hành Trung ương Đảng Cộng sản Việt Nam": 2,
    "Thể loại:Bí thư Tỉnh ủy Việt Nam": 2,
    # Chính phủ
    "Thể loại:Bộ trưởng Việt Nam": 2,
    "Thể loại:Thứ trưởng Việt Nam": 2,
    # Chính quyền địa phương
    "Thể loại:Chủ tịch Ủy ban nhân dân tỉnh Việt Nam": 2,
    "Thể loại:Chủ tịch Hội đồng nhân dân tỉnh Việt Nam": 2,
    # Quốc hội (các khóa gần đây)
    "Thể loại:Đại biểu Quốc hội Việt Nam khóa XIII": 1,
    "Thể loại:Đại biểu Quốc hội Việt Nam khóa XIV": 1,
    "Thể loại:Đại biểu Quốc hội Việt Nam khóa XV": 1,
    "Thể loại:Đại biểu Quốc hội Việt Nam khóa XVI": 1,
    # Lực lượng vũ trang (lãnh đạo Bộ Công an / Bộ Quốc phòng)
    "Thể loại:Thượng tướng Công an nhân dân Việt Nam": 1,
    "Thể loại:Trung tướng Công an nhân dân Việt Nam": 1,
    "Thể loại:Thượng tướng Quân đội nhân dân Việt Nam": 1,
    # Lãnh đạo tập đoàn nhà nước
    "Thể loại:Doanh nghiệp nhà nước Việt Nam": 2,
}

ORG_ROOTS = {
    "Thể loại:Doanh nghiệp nhà nước Việt Nam": 2,
    "Thể loại:Bộ của Việt Nam": 1,
    "Thể loại:Cơ quan ngang bộ Việt Nam": 1,
    "Thể loại:Cơ quan thuộc Chính phủ Việt Nam": 1,
    "Thể loại:Cơ quan Trung ương Đảng Cộng sản Việt Nam": 1,
    "Thể loại:Ủy ban của Quốc hội Việt Nam": 1,
}

ROMAN_OLD = r"khóa (I|II|III|IV|V|VI|VII|VIII|IX)\b"
EXCLUDE_CAT = re.compile(
    r"Việt Nam Cộng hòa|Cộng hòa miền Nam|Đế quốc|Quốc gia Việt Nam|Liên Xô|"
    r"Đông Dương|Pháp thuộc|thế kỷ 19|đã mất|" + ROMAN_OLD
)
# Trang không phải người (danh sách, chức vụ...)
NON_PERSON_TITLE = re.compile(r"^(Danh sách|Bộ |Ban |Ủy ban|Tập đoàn|Tổng công ty|Ngân hàng|Chính phủ|Quốc hội)")


def bfs(roots: dict[str, int]) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    seen = set()
    q = deque((c, d) for c, d in roots.items())
    while q:
        cat, depth = q.popleft()
        if cat in seen:
            continue
        seen.add(cat)
        try:
            members = category_members(cat)
        except Exception as e:  # thể loại không tồn tại -> bỏ qua
            print("  ! skip", cat, e)
            continue
        for m in members:
            if m["ns"] == 0:
                found.setdefault(m["title"], set()).add(cat)
            elif m["ns"] == 14 and depth > 0 and not EXCLUDE_CAT.search(m["title"]):
                q.append((m["title"], depth - 1))
        print(f"  {cat} -> tổng {len(found)} trang")
    return found


def main():
    people = bfs(PERSON_ROOTS)
    orgs = bfs(ORG_ROOTS)
    out = {}
    for t, cats in orgs.items():
        out[t] = {"kind": "org", "categories": sorted(cats)}
    for t, cats in people.items():
        if t in out:
            continue
        kind = "org" if NON_PERSON_TITLE.search(t) else "person"
        out[t] = {"kind": kind, "categories": sorted(cats)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_p = sum(1 for v in out.values() if v["kind"] == "person")
    print(f"Saved {OUT}: {len(out)} trang ({n_p} người ứng viên, {len(out) - n_p} tổ chức)")


if __name__ == "__main__":
    main()
