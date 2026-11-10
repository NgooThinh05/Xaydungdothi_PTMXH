// =====================================================================
// KỊCH BẢN LOAD CSV VÀO NEO4J (Đặt các file CSV trong thư mục `import` của Neo4j)
// =====================================================================

// 1. Tạo Constraints (Neo4j 5.x)
CREATE CONSTRAINT politician_name_unique IF NOT EXISTS FOR (p:Politician) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT role_name_unique IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT ban_nganh_name_unique IF NOT EXISTS FOR (b:BanNganh) REQUIRE b.name IS UNIQUE;
CREATE CONSTRAINT organization_name_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE;
CREATE CONSTRAINT province_name_unique IF NOT EXISTS FOR (pr:Province) REQUIRE pr.name IS UNIQUE;
CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (a:Article) REQUIRE a.article_id IS UNIQUE;

// 2. Nạp Nodes (:Politician)
LOAD CSV WITH HEADERS FROM 'file:///nodes_politicians.csv' AS row
MERGE (p:Politician {name: row.name})
SET p.honorific = row.honorific,
    p.primary_role = row.primary_role,
    p.role_title = row.role_title,
    p.primary_ban_nganh = row.primary_ban_nganh,
    p.ban_nganh = row.ban_nganh,
    p.primary_organization = row.primary_organization,
    p.organization = row.organization,
    p.primary_province = row.primary_province,
    p.province = row.province,
    p.total_articles = toInteger(row.total_articles),
    p.total_mentions = toInteger(row.total_mentions),
    p.main_character_count = toInteger(row.main_character_count),
    p.co_occurring_degree = toInteger(row.co_occurring_degree),
    p.top_co_occurring_politicians = row.top_co_occurring_politicians,
    p.sample_title = row.sample_title;

// 3. Nạp Nodes (:Role), (:BanNganh), (:Organization), (:Province), (:Article)
LOAD CSV WITH HEADERS FROM 'file:///nodes_roles.csv' AS row
MERGE (:Role {name: row.name});

LOAD CSV WITH HEADERS FROM 'file:///nodes_ban_nganh.csv' AS row
MERGE (:BanNganh {name: row.name});

LOAD CSV WITH HEADERS FROM 'file:///nodes_organizations.csv' AS row
MERGE (:Organization {name: row.name});

LOAD CSV WITH HEADERS FROM 'file:///nodes_provinces.csv' AS row
MERGE (:Province {name: row.name});

LOAD CSV WITH HEADERS FROM 'file:///nodes_articles.csv' AS row
MERGE (a:Article {article_id: row.article_id})
SET a.title = row.title,
    a.published_date = row.published_date,
    a.publisher = row.publisher,
    a.url = row.url;

// 4. Nạp Relationships
LOAD CSV WITH HEADERS FROM 'file:///rels_holds_role.csv' AS row
MATCH (p:Politician {name: row.person_name})
MATCH (r:Role {name: row.role_name})
MERGE (p)-[rel:HOLDS_ROLE]->(r)
SET rel.is_primary = (row.is_primary = 'True');

LOAD CSV WITH HEADERS FROM 'file:///rels_ban_nganh.csv' AS row
MATCH (p:Politician {name: row.person_name})
MATCH (b:BanNganh {name: row.ban_nganh_name})
MERGE (p)-[rel:BELONGS_TO_BAN_NGANH]->(b)
SET rel.is_primary = (row.is_primary = 'True');

LOAD CSV WITH HEADERS FROM 'file:///rels_works_at.csv' AS row
MATCH (p:Politician {name: row.person_name})
MATCH (o:Organization {name: row.organization_name})
MERGE (p)-[rel:WORKS_AT]->(o)
SET rel.is_primary = (row.is_primary = 'True');

LOAD CSV WITH HEADERS FROM 'file:///rels_province.csv' AS row
MATCH (p:Politician {name: row.person_name})
MATCH (pr:Province {name: row.province_name})
MERGE (p)-[rel:ASSOCIATED_WITH_PROVINCE]->(pr)
SET rel.is_primary = (row.is_primary = 'True');

LOAD CSV WITH HEADERS FROM 'file:///rels_appeared_in.csv' AS row
MATCH (p:Politician {name: row.person_name})
MATCH (a:Article {article_id: row.article_id})
MERGE (p)-[:APPEARED_IN]->(a);

LOAD CSV WITH HEADERS FROM 'file:///rels_co_occurs.csv' AS row
MATCH (p1:Politician {name: row.source_person})
MATCH (p2:Politician {name: row.target_person})
MERGE (p1)-[rel:CO_OCCURS_WITH]->(p2)
SET rel.weight = toInteger(row.weight),
    rel.shared_article_ids = row.shared_article_ids,
    rel.shared_organizations = row.shared_organizations,
    rel.shared_ban_nganh = row.shared_ban_nganh,
    rel.shared_provinces = row.shared_provinces;
