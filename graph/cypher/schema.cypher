// Ràng buộc & chỉ mục cho mạng Chính trị gia – Cơ quan nhà nước VN
CREATE CONSTRAINT person_id IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT org_id IF NOT EXISTS FOR (n:Organization) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT prov_id IF NOT EXISTS FOR (n:Province) REQUIRE n.id IS UNIQUE;
CREATE INDEX person_name IF NOT EXISTS FOR (n:Person) ON (n.name);
CREATE INDEX org_name IF NOT EXISTS FOR (n:Organization) ON (n.name);
CREATE INDEX org_type IF NOT EXISTS FOR (n:Organization) ON (n.type);
CREATE INDEX prov_name IF NOT EXISTS FOR (n:Province) ON (n.name);
CREATE CONSTRAINT chucvu_id IF NOT EXISTS FOR (n:ChucVu) REQUIRE n.id IS UNIQUE;
CREATE INDEX chucvu_name IF NOT EXISTS FOR (n:ChucVu) ON (n.name);
