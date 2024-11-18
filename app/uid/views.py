from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
#from uuid import uuid5, NAMESPACE_URL
import json, logging
from neomodel import db
from .models import UIDGenerator, UIDNode, Provider, LCVTerm, LanguageSet
from .forms import ProviderForm, LCVTermForm
from .models import report_all_uids, report_uids_by_echelon, GeneratedUIDLog
from rest_framework import viewsets
from rest_framework.response import Response

import os
from .forms import SearchForm
import requests
import urllib.parse

# Cypher Search Queries
SEARCH_BY_ALIAS = """
WITH toLower($search_term) as search_term
MATCH (a:NeoAlias)
WHERE toLower(a.alias) CONTAINS search_term
MATCH (a)-[:POINTS_TO]->(term:NeoTerm)
OPTIONAL MATCH (term)-[:POINTS_TO]->(def:NeoDefinition)
OPTIONAL MATCH (ctx:NeoContext)-[:IS_A]->(term)
RETURN term.uid as LCVID, a.alias as Alias, def.definition as Definition, ctx.context as Context
LIMIT 100
"""

SEARCH_BY_DEFINITION = """
WITH toLower($search_term) as search_term
MATCH (def:NeoDefinition)
WHERE toLower(def.definition) CONTAINS search_term
MATCH (term:NeoTerm)-[:POINTS_TO]->(def)
OPTIONAL MATCH (a:NeoAlias)-[:POINTS_TO]->(term)
OPTIONAL MATCH (ctx:NeoContext)-[:IS_A]->(term)
RETURN term.uid as LCVID, a.alias as Alias, def.definition as Definition, ctx.context as Context
LIMIT 100
"""

SEARCH_BY_CONTEXT = """
WITH toLower($search_term) as search_term
MATCH (ctx:NeoContext)
WHERE toLower(ctx.context) CONTAINS search_term
MATCH (ctx)-[:IS_A]->(term:NeoTerm)
OPTIONAL MATCH (term)-[:POINTS_TO]->(def:NeoDefinition)
OPTIONAL MATCH (a:NeoAlias)-[:POINTS_TO]->(term)
RETURN term.uid as LCVID, a.alias as Alias, def.definition as Definition, ctx.context as Context
LIMIT 100
"""

GENERAL_GRAPH_SEARCH = """
WITH toLower($search_term) as search_term
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
RETURN * LIMIT 100
"""

# Globally Declare variable for children
MAX_CHILDREN = 2**32 -1

# Set up logging to capture errors and important information
logger = logging.getLogger(__name__)

# Attempt to initialize the UID generator
try:
    uid_generator = UIDGenerator()
except RuntimeError as e:
    # Log an error if UIDGenerator fails to initialize (e.g., due to Neo4j connection issues)
    logger.error(f"Failed to initialize UIDGenerator: {e}")
    uid_generator = None  # Handle initialization failure appropriately

def execute_neo4j_query(query, params):
    query_str = query
    try:
        logger.info(f"Executing query: {query} with params: {params}")
        results, meta = db.cypher_query(query_str, params)
        return results
    except Exception as e:
        logger.error(f"Error executing Neo4j query: {e}")
        return None

# Django view for search functionality
def search(request):
    results = []
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data['search_term']
            search_type = form.cleaned_data['search_type']

            # Log form data for debugging
            logger.info(f"Search form data: search_term={search_term}, search_type={search_type}")

            # Determine which query to use based on search type
            if search_type == 'alias':
                query = SEARCH_BY_ALIAS
            elif search_type == 'definition':
                query = SEARCH_BY_DEFINITION
            elif search_type == 'context':
                query = SEARCH_BY_CONTEXT
            else:
                query = GENERAL_GRAPH_SEARCH  # For 'general' search

            # Log the query and params being sent to Neo4j
            logger.info(f"Executing query: {query} with params: {{'search_term': {search_term}}}")

            # Execute the query
            results_data = execute_neo4j_query(query, {"search_term": search_term})

            if results_data:
                logger.info(f"Raw results data: {results_data}")
                results = [
                    {
                        "LCVID": record.get('LCVID', 'No LCVID'),  # Use get() to avoid KeyError
                        "Alias": record.get('Alias', 'No alias'),
                        "Definition": record.get('Definition', 'No definition'),
                        "Context": record.get('Context', 'No context')  # Handle missing context
                    }
                    #for record in results_data['results'][0]['data']
                    for record in results_data:
                        uid = record[0]
                        alias = record[1]
                        definition = record[2]
                        context = record[3]
                ]
            else:
                logger.info("No results found.")
                results = [{'error': 'No results found or error querying Neo4j.'}]

    else:
        form = SearchForm()

    return render(request, 'search.html', {'form': form, 'results': results})

# Create your views here.
def generate_uid_node(request: HttpRequest):
    request_body = json.loads(request.body)
    print(request_body)
    strict_parent_validation = request_body.get('strict_parent_validation', False)
    parent_uid = request_body.get('parent_uid', None)
    namespace = request_body.get('namespace', 'LCV') #??? Ask Hunter about where namespace is actually configured and is it different than just organization?
    echelon_level = request_body.get('echelon_level', 'level_1')  # Get echelon level from request
    
    parent_node = UIDNode.get_node_by_uid(parent_uid, namespace, echelon_level='parent_level') #added namespace and parent level

    if parent_node is None:
        if strict_parent_validation:
            return HttpResponse("{ 'error': 'Parent node not found' }", status=404, content_type='application/json')
        else:
            parent_node = UIDNode.create_node(uid = parent_uid, namespace = namespace)
    
    num_children = parent_node.children.count()

    # Count children using a loop
    num_children = 0
    for child in parent_node.children:
       num_children += 1

    if num_children > MAX_CHILDREN:
        return HttpResponse("{ 'error': 'Max children exceeded for {parent_uid}' }", status=400, content_type='application/json')
    local_uid = uid_generator.generate_uid() # updated to use new UID Generation method
    #local_uid = CounterNode.increment().counter

    new_child_node = UIDNode.create_node(uid = local_uid, namespace = namespace, echelon_level=echelon_level)

    parent_node.children.connect(new_child_node)

    return HttpResponse("{ 'uid': '" + str(local_uid) + "' }", content_type='application/json')


# Provider and LCVTerm (Otherwise alternative Parent and child) Now with collision detection on both.
def create_provider(request):
    if request.method == 'POST':
        form = ProviderForm(request.POST)
        if form.is_valid():
            provider = form.save()
            provider.uid = uid_generator.generate_uid()  # Ensure UID is generated
            provider.save()
            return redirect('uid:success')
    else:
        form = ProviderForm()
    return render(request, 'create_provider.html', {'form': form})

def create_lcvterm(request):
    if request.method == 'POST':
        form = LCVTermForm(request.POST)
        if form.is_valid():
            lcvterm = form.save()
            lcvterm.uid = uid_generator.generate_uid()  # Ensure UID is generated
            lcvterm.save()
            return redirect('uid:success')
    else:
        form = LCVTermForm()
    return render(request, 'create_lcvterm.html', {'form': form})

def success_view(request):
    return render(request, 'success.html', {'message': 'Operation completed successfully!'})

# Report Generation by echelon
def generate_report(request, echelon_level=None):
    if echelon_level == "root": # Getting all root level UID for echelon report
       uids = report_all_uids()
    else:
       # Retrieve UIDs based on the specified echelon level
       uids = report_uids_by_echelon(echelon_level)

    return JsonResponse({'uids': uids})

# Create API endpoint to share current UID repo
class UIDRepoViewSet(viewsets.ViewSet):
    def list(self, request):
        # Retrieve all UIDs from the GeneratedUIDLog model
        uids = GeneratedUIDLog.objects.all()
        uid_data = [{'uid': log.uid, 'generated_at': log.generated_at, 'generator_id': log.generator_id} for log in uids]
        return Response(uid_data)
    
# Postman view
def export_to_postman(request, uid):
    try:
        provider = Provider.objects.get(uid=uid)
        data = {
            'name': provider.name,
            'uid': provider.uid,
            'echelon level':provider.echelon_level,
            # Add additional fields you want to export
        }
    except Provider.DoesNotExist:
        try:
            lcv_term = LCVTerm.objects.get(uid=uid)
            data = {
                'name': lcv_term.name,
                'uid': lcv_term.uid,
                'echelon level':lcv_term.echelon_level,
                # Add additional fields you want to export
            }
        except LCVTerm.DoesNotExist:
            try:
                with db.transaction:
                    #language_set = LanguageSet.objects.get(uid=uid)
                    language_set = LanguageSet.nodes.get(uid=uid)
                    data = {
                        'name': language_set.name,
                        'uid': language_set.uid,
                        'terms': [term.uid for term in language_set.terms], # this should update Postman on LanguageSet changes to a Node.
                        #'terms': [term.uid for term in language_set.terms.all()],
                }
            except LanguageSet.DoesNotExist:
                return JsonResponse({'error': 'UID not found'}, status=404)

    return JsonResponse(data)