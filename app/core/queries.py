SEARCH_BY_ALIAS = """
WITH toLower('changeme') as search_term

MATCH (a:NeoAlias)
WHERE toLower(a.alias) CONTAINS search_term
MATCH (a)-[:POINTS_TO]->(term:NeoTerm)
OPTIONAL MATCH (term)-[:POINTS_TO]->(def:NeoDefinition)
OPTIONAL MATCH (ctx:NeoContext)-[:IS_A]->(term)
RETURN 
    term.uid as LCVID,
    a.alias as Alias,
    def.definition as Definition,
    ctx.context as Context
LIMIT 100
"""

SEARCH_BY_DEFINITION = """
WITH toLower('changeme') as search_term

MATCH (def:NeoDefinition)
WHERE toLower(def.definition) CONTAINS search_term
MATCH (term:NeoTerm)-[:POINTS_TO]->(def)
OPTIONAL MATCH (a:NeoAlias)-[:POINTS_TO]->(term)
OPTIONAL MATCH (ctx:NeoContext)-[:IS_A]->(term)
RETURN
    term.uid as LCVID,
    a.alias as Alias,
    def.definition as Definition,
    ctx.context as Context
LIMIT 100
"""

SEARCH_BY_CONTEXT = """
WITH toLower('changeme') as search_term

MATCH (ctx:NeoContext)
WHERE toLower(ctx.context) CONTAINS search_term
MATCH (ctx)-[:IS_A]->(term:NeoTerm)
OPTIONAL MATCH (term)-[:POINTS_TO]->(def:NeoDefinition)
OPTIONAL MATCH (a:NeoAlias)-[:POINTS_TO]->(term)
RETURN
    term.uid as LCVID,
    a.alias as Alias,
    def.definition as Definition,
    ctx.context as Context
LIMIT 100
"""

GENERAL_GRAPH_SEARCH = """
// searches aliases, definitions, and contexts
// returns all connected nodes and paths
WITH toLower('changeme') as search_term

MATCH (n)
WHERE (n:NeoAlias OR n:NeoDefinition OR n:NeoContext) 
  AND (
    (n:NeoAlias AND toLower(n.alias) CONTAINS search_term) OR
    (n:NeoDefinition AND toLower(n.definition) CONTAINS search_term) OR
    (n:NeoContext AND toLower(n.context) CONTAINS search_term)
  )
WITH n
CALL {
    WITH n
    MATCH path = (n)-[*1..2]-(connected)
    RETURN path
}
RETURN *
LIMIT 100
"""
