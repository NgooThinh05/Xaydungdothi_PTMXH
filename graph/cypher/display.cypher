// Thuộc tính dùng riêng cho HIỂN THỊ trên Neo4j Browser (đặt Caption = hien_thi / nhan).
// Chạy sau khi nạp xong nút & cạnh (graph/load_neo4j.py tự gọi).

// 1) Tên cơ quan rút gọn
MATCH (o:Organization)
SET o.hien_thi = replace(replace(replace(replace(o.name,
      'Ủy ban nhân dân', 'UBND'), 'Hội đồng nhân dân', 'HĐND'),
      'Ủy ban Mặt trận Tổ quốc Việt Nam', 'UBMTTQ'), 'Ban Chấp hành Trung ương Đảng', 'BCH Trung ương Đảng')
    + CASE WHEN o.cu_the = false THEN ' (chưa rõ tỉnh)' ELSE '' END;

MATCH (t:Province) SET t.hien_thi = t.name + CASE WHEN t.status = 'đã sáp nhập' THEN ' (cũ)' ELSE '' END;

// 2) Chức vụ hiện tại của mỗi người (tối đa 2), qua nút ChucVu. Ưu tiên Wikipedia (nhiệm kỳ chưa kết thúc),
//    sau đó tin tức (không "nguyên", nhắc >= 2 lần hoặc người chỉ có trong tin tức), chức vụ điều hành trước "Ủy viên/Đại biểu"
MATCH (p:Person)
OPTIONAL MATCH (p)-[r:GIU_CHUC_VU]->(c:ChucVu)
WHERE (r.source STARTS WITH 'wikipedia' AND coalesce(r.end, '') = '')
   OR (NOT r.source STARTS WITH 'wikipedia' AND r.current = true AND (coalesce(r.weight, 1) >= 2 OR p.source = 'news'))
WITH p, r, c,
     CASE WHEN r.source STARTS WITH 'wikipedia' THEN 0 ELSE 1 END AS nguon,
     CASE WHEN c.kind = 'Thành viên' OR c.org_name STARTS WITH 'Hội đồng Quốc phòng' THEN 1 ELSE 0 END AS phu
ORDER BY nguon, phu, r.start DESC
WITH p, [x IN collect(replace(c.hien_thi, ' · ', ' ')) WHERE x IS NOT NULL] AS cv0
WITH p, reduce(acc = [], x IN cv0 | CASE WHEN x IN acc THEN acc ELSE acc + x END)[0..2] AS cv
SET p.chuc_vu = CASE WHEN size(cv) = 0 THEN NULL ELSE reduce(s = cv[0], x IN cv[1..] | s + '; ' + x) END;

// người không còn chức vụ hiện tại -> chức vụ gần nhất, ghi "nguyên"
MATCH (p:Person) WHERE p.chuc_vu IS NULL
OPTIONAL MATCH (p)-[r:GIU_CHUC_VU]->(c:ChucVu)
WHERE r.source STARTS WITH 'wikipedia' OR coalesce(r.weight, 1) >= 2 OR p.source = 'news'
WITH p, c ORDER BY coalesce(r.end, r.start) DESC
WITH p, head(collect(replace(c.hien_thi, ' · ', ' '))) AS cv
SET p.chuc_vu = CASE WHEN cv IS NULL THEN NULL ELSE 'nguyên ' + cv END;

MATCH (p:Person) WHERE p.chuc_vu IS NOT NULL
SET p.chuc_vu = replace(replace(p.chuc_vu, 'Trưởng Ban Ban ', 'Trưởng Ban '), 'Trưởng ban Ban ', 'Trưởng Ban ');

MATCH (p:Person)
SET p.hien_thi = p.name + CASE WHEN p.chuc_vu IS NULL THEN '' ELSE ' · ' + p.chuc_vu END;

// 3) Nhãn cạnh: GIU_CHUC_VU chỉ ghi nhiệm kỳ (chức danh nằm ở nút ChucVu)
MATCH ()-[r:GIU_CHUC_VU]->()
SET r.nhan = CASE WHEN coalesce(r.start, '') = '' THEN 'giữ chức'
                  ELSE left(r.start, 4) + '–' +
                       CASE WHEN coalesce(r.end, '') <> '' THEN left(r.end, 4)
                            WHEN r.current = false THEN '?' ELSE 'nay' END END;

MATCH ()-[r]->()
WHERE type(r) <> 'GIU_CHUC_VU'
WITH r, {THUOC_CO_QUAN: 'thuộc', LANH_DAO_TRUC_TIEP: 'cấp trên của', CAP_PHO: 'cấp phó của', KE_NHIEM: 'kế nhiệm', QUE_QUAN: 'quê',
         THUOC_DIA_PHUONG: 'thuộc tỉnh', TRUC_THUOC: 'trực thuộc', HOP_NHAT_VAO: 'hợp nhất vào',
         CHU_TRI: 'chủ trì', CHI_DAO: 'chỉ đạo', BO_NHIEM: 'bổ nhiệm', DIEU_DONG: 'điều động',
         MIEN_NHIEM: 'miễn nhiệm', THANH_TRA: 'thanh tra', KIEM_TRA: 'kiểm tra', KY_LUAT: 'kỷ luật',
         PARENT_OF: 'cha/mẹ của', SPOUSE_OF: 'vợ/chồng', SIBLING_OF: 'anh/chị/em', NOI_SINH: 'sinh tại',
         LAM_VIEC_VOI: 'làm việc với', PHOI_HOP: 'phối hợp'} AS vi
SET r.nhan = coalesce(vi[type(r)], type(r)) +
    CASE WHEN type(r) = 'KE_NHIEM' AND coalesce(r.role, '') <> '' THEN ' (' + split(r.role, '; ')[0] + ')' ELSE '' END +
    CASE WHEN r.weight > 1 AND NOT type(r) IN ['KE_NHIEM', 'LANH_DAO_TRUC_TIEP', 'CAP_PHO'] THEN ' ×' + toString(r.weight) ELSE '' END +
    CASE WHEN coalesce(r.event_date, r.date, '') <> '' THEN ' · ' + left(coalesce(r.event_date, r.date), 7) ELSE '' END;
