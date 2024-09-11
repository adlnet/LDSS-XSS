from neomodel import db
from django.http import HttpResponse

def check_neo4j_connection(request):
    try:
        db.cypher_query("MATCH (n) RETURN n LIMIT 1")
        return HttpResponse("Neo4j is connected")
    except Exception as e:
        return HttpResponse("Neo4j is not connected: " + str(e))