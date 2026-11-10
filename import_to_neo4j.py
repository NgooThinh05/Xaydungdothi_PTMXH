# -*- coding: utf-8 -*-
"""
NẠP ĐỒ THỊ MẠNG LƯỚI CHÍNH TRỊ GIA VIỆT NAM VÀO NEO4J DATABASE
================================================================
Script kết nối trực tiếp vào Neo4j và nạp Đồ thị Chính trị gia gồm:
- Node duy nhất: (:Politician) - 2,284 chính trị gia Việt Nam
- 3 loại Cạnh nối giữa các (:Politician):
  1. [:CO_OCCURS_WITH] : Cùng xuất hiện trong bài báo (kèm trọng số `weight` và `shared_article_ids`)
  2. [:SAME_BAN_NGANH] : Cùng công tác trong một Ban ngành / Lĩnh vực
  3. [:SAME_PROVINCE]  : Cùng công tác tại một Tỉnh / Thành phố
"""

import os
import json
from itertools import combinations
from collections import defaultdict
from neo4j import GraphDatabase


INPUT_PROFILES_JSON = "baomoi_vn_politicians_profiles.json"

NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
NEO4J_DATABASE = "neo4j"

# Các nhãn ban ngành địa phương chung cần gắn kèm tên Tỉnh/Thành để không nối nhầm giữa các tỉnh khác nhau
LOCAL_GENERIC_BAN_NGANH = {
    "Chính quyền cấp tỉnh/thành phố",
    "Chính quyền cấp quận/huyện",
    "Chính quyền cấp xã/phường",
    "HĐND cấp tỉnh/thành phố",
    "HĐND cấp quận/huyện",
    "HĐND cấp xã/phường",
    "Khối Đảng Tỉnh ủy",
    "Khối Đảng Thành ủy",
    "Khối Đảng Huyện ủy",
    "Khối Đảng Quận ủy",
    "Khối Đảng Thị ủy",
    "Đảng bộ cấp cơ sở",
}

# Các nhãn khối vĩ mô quá rộng (chỉ dùng khi nhân vật không có ban ngành chuyên môn cụ thể hơn)
MACRO_BLOCKS = {
    "Khối Đảng Trung ương",
    "Khối Chính phủ",
    "Khối Quốc hội",
    "Khối Mặt trận - Đoàn thể",
}

# Các chức danh lãnh đạo cấp cao Trung ương (tránh gán nhầm tỉnh đi thăm làm tỉnh công tác cố định)
PURE_CENTRAL_ROLES = {
    "Tổng Bí thư",
    "Nguyên Tổng Bí thư",
    "Chủ tịch nước",
    "Phó Chủ tịch nước",
    "Nguyên Chủ tịch nước",
    "Thủ tướng Chính phủ",
    "Phó Thủ tướng Thường trực Chính phủ",
    "Phó Thủ tướng Chính phủ",
    "Nguyên Thủ tướng Chính phủ",
    "Chủ tịch Quốc hội",
    "Phó Chủ tịch Thường trực Quốc hội",
    "Phó Chủ tịch Quốc hội",
    "Nguyên Chủ tịch Quốc hội",
    "Thường trực Ban Bí thư",
    "Bộ trưởng",
    "Thứ trưởng Thường trực",
    "Thứ trưởng",
    "Thống đốc Ngân hàng Nhà nước",
    "Tổng Thanh tra Chính phủ",
    "Tổng Kiểm toán Nhà nước",
}

LOCAL_ROLE_KEYWORDS = (
    "tỉnh ủy", "thành ủy", "huyện ủy", "quận ủy", "thị ủy", "đảng ủy xã", "đảng ủy phường",
    "ubnd", "hđnd", "sở ", "công an tỉnh", "công an thành phố", "đoàn đbqh", "mttq",
)


def get_work_province(node: dict) -> str:
    """
    Xác định tỉnh/thành công tác chính của nhân vật.
    Nếu là lãnh đạo thuần Trung ương (không giữ chức vụ địa phương) thì không gán tỉnh đi công tác làm tỉnh biên chế.
    """
    primary_prov = node.get("primary_province", "").strip()
    if not primary_prov:
        return ""

    roles_set = set(node.get("roles_list", []))
    role_title_low = node.get("role_title", "").lower()
    org_low = node.get("organization", "").lower()

    has_local_attachment = any(k in role_title_low or k in org_low for k in LOCAL_ROLE_KEYWORDS)
    if (roles_set & PURE_CENTRAL_ROLES) and not has_local_attachment:
        return ""

    return primary_prov


def get_effective_ban_nganh_set(node: dict, work_prov: str) -> set[str]:
    """
    Chuẩn hóa danh sách ban ngành công tác của nhân vật để kết nối cạnh [:SAME_BAN_NGANH] chính xác:
    - Nếu là ban ngành chung cấp địa phương (VD: 'Chính quyền cấp tỉnh/thành phố'), gắn kèm tên tỉnh/thành.
    - Ưu tiên ban ngành chuyên môn cụ thể hơn các khối vĩ mô chung.
    """
    raw_bns = [b.strip() for b in node.get("ban_nganh_list", []) if b.strip()]
    if not raw_bns:
        return set()

    specific_bns = [b for b in raw_bns if b not in MACRO_BLOCKS]
    selected_bns = specific_bns if specific_bns else raw_bns[:1]

    effective = set()
    for b in selected_bns[:2]:  # Lấy tối đa 2 ban ngành chính của nhân vật
        if b in LOCAL_GENERIC_BAN_NGANH:
            if work_prov:
                effective.add(f"{b} ({work_prov})")
        else:
            effective.add(b)
    return effective


def load_politicians_graph_from_json(json_path: str, max_peers_per_group: int = 20) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """
    Đọc `baomoi_vn_politicians_profiles.json` và tạo:
    1. Danh sách Nodes (:Politician)
    2. Danh sách Cạnh [:CO_OCCURS_WITH] (Đồng xuất hiện trong bài báo)
    3. Danh sách Cạnh [:SAME_BAN_NGANH] (Cùng ban ngành công tác)
    4. Danh sách Cạnh [:SAME_PROVINCE]  (Cùng tỉnh/thành công tác)
    """
    with open(json_path, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    politician_nodes = []
    pol_lookup = {}
    article_to_politicians = defaultdict(set)
    ban_nganh_groups = defaultdict(list)
    province_groups = defaultdict(list)

    for item in profiles:
        name = str(item.get("person_name", "")).strip()
        if not name:
            continue

        roles_list = [str(r).strip() for r in item.get("roles_list", []) if str(r).strip()]
        ban_nganh_list = [str(b).strip() for b in item.get("ban_nganh_list", []) if str(b).strip()]
        org_list = [str(o).strip() for o in item.get("organization_list", []) if str(o).strip()]
        prov_list = [str(p).strip() for p in item.get("provinces_list", []) if str(p).strip()]
        article_ids = [str(a).strip() for a in item.get("article_ids", []) if str(a).strip()]
        sample_titles = [str(t).strip() for t in item.get("sample_article_titles", []) if str(t).strip()]

        node_data = {
            "name": name,
            "honorific": str(item.get("honorific", "")).strip(),
            "primary_role": roles_list[0] if roles_list else str(item.get("role_title", "")).strip(),
            "role_title": str(item.get("role_title", "")).strip(),
            "roles_list": roles_list,
            "primary_ban_nganh": ban_nganh_list[0] if ban_nganh_list else str(item.get("ban_nganh", "")).strip(),
            "ban_nganh": str(item.get("ban_nganh", "")).strip(),
            "ban_nganh_list": ban_nganh_list,
            "primary_organization": org_list[0] if org_list else str(item.get("organization", "")).strip(),
            "organization": str(item.get("organization", "")).strip(),
            "organization_list": org_list,
            "primary_province": prov_list[0] if prov_list else str(item.get("province", "")).strip(),
            "province": str(item.get("province", "")).strip(),
            "provinces_list": prov_list,
            "total_articles": int(item.get("total_articles", len(article_ids))),
            "total_mentions": int(item.get("total_mentions", 1)),
            "main_character_count": int(item.get("main_character_count", 0)),
            "co_occurring_degree": int(item.get("co_occurring_degree", 0)),
            "top_co_occurring_politicians": str(item.get("top_co_occurring_politicians", "")).strip(),
            "article_ids": article_ids,
            "sample_article_titles": sample_titles,
        }

        work_prov = get_work_province(node_data)
        node_data["work_province"] = work_prov
        politician_nodes.append(node_data)
        pol_lookup[name] = node_data

        for aid in article_ids:
            article_to_politicians[aid].add(name)

        if work_prov:
            province_groups[work_prov].append(name)

        for eff_bn in get_effective_ban_nganh_set(node_data, work_prov):
            ban_nganh_groups[eff_bn].append(name)

    # 1. Xây dựng cạnh [:CO_OCCURS_WITH]
    pair_shared_articles = defaultdict(list)
    for aid, p_names in article_to_politicians.items():
        if len(p_names) >= 2:
            for u, v in combinations(sorted(p_names), 2):
                pair_shared_articles[(u, v)].append(aid)

    co_occurs_edges = []
    for (u, v), shared_aids in pair_shared_articles.items():
        u_node = pol_lookup[u]
        v_node = pol_lookup[v]
        shared_orgs = sorted(set(u_node["organization_list"]) & set(v_node["organization_list"]))
        shared_bns = sorted(set(u_node["ban_nganh_list"]) & set(v_node["ban_nganh_list"]))
        shared_provs = sorted(set(u_node["provinces_list"]) & set(v_node["provinces_list"]))

        co_occurs_edges.append({
            "source_person": u,
            "target_person": v,
            "weight": len(shared_aids),
            "shared_article_ids": shared_aids,
            "shared_organizations": ", ".join(shared_orgs),
            "shared_ban_nganh": ", ".join(shared_bns),
            "shared_provinces": ", ".join(shared_provs),
        })
    co_occurs_edges.sort(key=lambda x: x["weight"], reverse=True)

    # Hàm sinh các cặp trong một nhóm (Ban ngành hoặc Tỉnh thành) có kiểm soát mật độ cạnh
    def generate_group_pairs(members: list[str]) -> list[tuple[str, str]]:
        # Sắp xếp thành viên theo số bài báo & lượt nhắc giảm dần (nhân vật trung tâm đứng đầu)
        sorted_members = sorted(
            members,
            key=lambda m: (pol_lookup[m]["total_articles"], pol_lookup[m]["total_mentions"], pol_lookup[m]["co_occurring_degree"]),
            reverse=True,
        )
        n = len(sorted_members)
        if n <= 1:
            return []
        if n <= max_peers_per_group:
            return [tuple(sorted((u, v))) for u, v in combinations(sorted_members, 2)]

        # Nếu nhóm rất lớn (> max_peers_per_group), kết nối các hạt nhân đầu nhóm với toàn nhóm
        # và kết nối mỗi thành viên với các thành viên lân cận cùng cơ quan/cấp bậc
        pairs = set()
        core_hubs = sorted_members[:5]
        for hub in core_hubs:
            for member in sorted_members:
                if hub != member:
                    pairs.add(tuple(sorted((hub, member))))
        for idx, u in enumerate(sorted_members):
            for v in sorted_members[idx + 1 : idx + 6]:
                pairs.add(tuple(sorted((u, v))))
        return list(pairs)

    # 2. Xây dựng cạnh [:SAME_BAN_NGANH]
    pair_ban_nganh = defaultdict(set)
    for bn_name, members in ban_nganh_groups.items():
        for u, v in generate_group_pairs(members):
            pair_ban_nganh[(u, v)].add(bn_name)

    same_ban_nganh_edges = []
    for (u, v), bn_set in pair_ban_nganh.items():
        bn_sorted = sorted(bn_set)
        same_ban_nganh_edges.append({
            "source_person": u,
            "target_person": v,
            "ban_nganh": ", ".join(bn_sorted),
            "ban_nganh_list": bn_sorted,
            "weight": len(bn_sorted),
        })

    # 3. Xây dựng cạnh [:SAME_PROVINCE]
    pair_provinces = defaultdict(set)
    for prov_name, members in province_groups.items():
        for u, v in generate_group_pairs(members):
            pair_provinces[(u, v)].add(prov_name)

    same_province_edges = []
    for (u, v), prov_set in pair_provinces.items():
        prov_sorted = sorted(prov_set)
        u_node = pol_lookup[u]
        v_node = pol_lookup[v]
        shared_orgs = sorted(set(u_node["organization_list"]) & set(v_node["organization_list"]))
        same_province_edges.append({
            "source_person": u,
            "target_person": v,
            "province": ", ".join(prov_sorted),
            "shared_organizations": ", ".join(shared_orgs),
            "weight": len(prov_sorted),
        })

    return politician_nodes, co_occurs_edges, same_ban_nganh_edges, same_province_edges


def import_politicians_to_neo4j(
    politician_nodes: list[dict],
    co_occurs_edges: list[dict],
    same_ban_nganh_edges: list[dict],
    same_province_edges: list[dict],
    uri: str = NEO4J_URI,
    user: str = NEO4J_USER,
    password: str = NEO4J_PASSWORD,
    database: str = NEO4J_DATABASE,
    batch_size: int = 500,
):
    """Xóa dữ liệu cũ và nạp đồ thị các chính trị gia cùng 3 loại cạnh vào Neo4j."""
    print(f"[*] Đang kết nối tới Neo4j tại {uri} (User: '{user}', Database: '{database}')...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
    except Exception as e:
        driver.close()
        print(f"\n[!] Lỗi kết nối / xác thực Neo4j ({uri}): {e}")
        print("    -> Hãy kiểm tra lại NEO4J_USER / NEO4J_PASSWORD tại dòng 21-24 trong file `import_to_neo4j.py` rồi chạy lại `python import_to_neo4j.py`.")
        return

    def run_batches(session, query: str, rows: list[dict], label: str):
        for i in range(0, len(rows), batch_size):
            session.run(query, batch=rows[i : i + batch_size])
        print(f"  + Đã nạp {len(rows):,} {label}")

    with driver.session(database=database) as session:
        # 1. Xóa dữ liệu cũ
        print("  -> Đang làm sạch dữ liệu cũ trong Neo4j...")
        session.run("MATCH (n) DETACH DELETE n")

        # 2. Tạo Unique Constraint cho (:Politician)
        session.run(
            "CREATE CONSTRAINT politician_name_unique IF NOT EXISTS "
            "FOR (p:Politician) REQUIRE p.name IS UNIQUE"
        )

        # 3. Nạp các Node (:Politician)
        node_query = """
        UNWIND $batch AS row
        MERGE (p:Politician {name: row.name})
        SET p.honorific = row.honorific,
            p.primary_role = row.primary_role,
            p.role_title = row.role_title,
            p.roles_list = row.roles_list,
            p.primary_ban_nganh = row.primary_ban_nganh,
            p.ban_nganh = row.ban_nganh,
            p.ban_nganh_list = row.ban_nganh_list,
            p.primary_organization = row.primary_organization,
            p.organization = row.organization,
            p.organization_list = row.organization_list,
            p.primary_province = row.primary_province,
            p.work_province = row.work_province,
            p.province = row.province,
            p.provinces_list = row.provinces_list,
            p.total_articles = row.total_articles,
            p.total_mentions = row.total_mentions,
            p.main_character_count = row.main_character_count,
            p.co_occurring_degree = row.co_occurring_degree,
            p.top_co_occurring_politicians = row.top_co_occurring_politicians,
            p.article_ids = row.article_ids,
            p.sample_article_titles = row.sample_article_titles
        """
        run_batches(session, node_query, politician_nodes, "Nodes (:Politician)")

        # 4. Nạp Cạnh [:CO_OCCURS_WITH] (Đồng xuất hiện trên báo)
        co_occurs_query = """
        UNWIND $batch AS row
        MATCH (p1:Politician {name: row.source_person})
        MATCH (p2:Politician {name: row.target_person})
        MERGE (p1)-[r:CO_OCCURS_WITH]->(p2)
        SET r.weight = row.weight,
            r.shared_article_ids = row.shared_article_ids,
            r.shared_organizations = row.shared_organizations,
            r.shared_ban_nganh = row.shared_ban_nganh,
            r.shared_provinces = row.shared_provinces
        """
        run_batches(session, co_occurs_query, co_occurs_edges, "Cạnh [:CO_OCCURS_WITH] (Đồng xuất hiện)")

        # 5. Nạp Cạnh [:SAME_BAN_NGANH] (Cùng Ban ngành công tác)
        ban_nganh_query = """
        UNWIND $batch AS row
        MATCH (p1:Politician {name: row.source_person})
        MATCH (p2:Politician {name: row.target_person})
        MERGE (p1)-[r:SAME_BAN_NGANH]->(p2)
        SET r.ban_nganh = row.ban_nganh,
            r.ban_nganh_list = row.ban_nganh_list,
            r.weight = row.weight
        """
        run_batches(session, ban_nganh_query, same_ban_nganh_edges, "Cạnh [:SAME_BAN_NGANH] (Cùng Ban ngành)")

        # 6. Nạp Cạnh [:SAME_PROVINCE] (Cùng Tỉnh/Thành công tác)
        province_query = """
        UNWIND $batch AS row
        MATCH (p1:Politician {name: row.source_person})
        MATCH (p2:Politician {name: row.target_person})
        MERGE (p1)-[r:SAME_PROVINCE]->(p2)
        SET r.province = row.province,
            r.shared_organizations = row.shared_organizations,
            r.weight = row.weight
        """
        run_batches(session, province_query, same_province_edges, "Cạnh [:SAME_PROVINCE] (Cùng Tỉnh/Thành)")

    driver.close()
    total_edges = len(co_occurs_edges) + len(same_ban_nganh_edges) + len(same_province_edges)
    print(f"\n[HOÀN TẤT] Đã nạp {len(politician_nodes):,} Chính trị gia và tổng cộng {total_edges:,} Cạnh vào Neo4j!")


def main():
    if not os.path.exists(INPUT_PROFILES_JSON):
        print(f"[!] Không tìm thấy file '{INPUT_PROFILES_JSON}'.")
        return

    print(f"[*] Đang đọc dữ liệu và tạo các loại cạnh từ '{INPUT_PROFILES_JSON}'...")
    nodes, co_edges, bn_edges, prov_edges = load_politicians_graph_from_json(INPUT_PROFILES_JSON)

    print(f"  -> Số lượng Chính trị gia (:Politician) : {len(nodes):,} nodes")
    print(f"  -> Cạnh đồng xuất hiện [:CO_OCCURS_WITH]: {len(co_edges):,} cạnh")
    print(f"  -> Cạnh cùng Ban ngành [:SAME_BAN_NGANH]: {len(bn_edges):,} cạnh")
    print(f"  -> Cạnh cùng Tỉnh/Thành [:SAME_PROVINCE]: {len(prov_edges):,} cạnh")

    import_politicians_to_neo4j(nodes, co_edges, bn_edges, prov_edges)


if __name__ == "__main__":
    main()
