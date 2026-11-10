// In Neo4j Browser, set a person's id first (run this as a separate command):
// :param personId => 'per:example'
// Then run the query below and switch the result frame to Graph.
// Click a node for details; double-click or right-click to expand it.
MATCH (person:Person {id: $personId})
OPTIONAL MATCH (person)-[relation]-(neighbor)
WITH person, relation, neighbor
ORDER BY coalesce(relation.event_date, relation.date, relation.start, '') DESC
LIMIT 150
OPTIONAL MATCH (neighbor:ChucVu)-[belongs:THUOC_CO_QUAN]->(organization:Organization)
RETURN person, relation, neighbor, belongs, organization;
