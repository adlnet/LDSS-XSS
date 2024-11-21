from django.shortcuts import render

from core.models import NeoDefinition
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from typing import List
from uuid import uuid4

from django.shortcuts import render, redirect
from django.contrib import messages
from neomodel import db
import logging
from django.urls import reverse

from .node_utils import create_vector_index, find_colliding_definition_nodes, find_similar_text_by_embedding, generate_embedding, evaluate_deconfliction_status, get_terms_with_multiple_definitions
from core.models import NeoDefinition, NeoTerm
logger = logging.getLogger('dict_config_logger')


def run_deconfliction(alias: str, definition: str, context: str, context_description: str):
    try:
        logger.info('Running Deconfliction')
        definition_vector_embedding = generate_embedding(definition)
        create_vector_index('definitions', 'NeoDefinition', 'embedding')
        results = find_similar_text_by_embedding(definition_vector_embedding, 'definition', 'definitions')
        deconfliction_status, most_similar_text, highest_score = evaluate_deconfliction_status(results)
        if deconfliction_status == 'unique':
            return definition_vector_embedding, deconfliction_status, None, None
        return definition_vector_embedding, deconfliction_status, most_similar_text, highest_score
    except Exception as e:
        logger.error(f"Error in run_deconfliction: {e}")
        raise e
    
def deconfliction_admin_view(request):
    duplicates = get_duplicate_definitions()
    collisions = find_colliding_definition_nodes()
    deviations = get_terms_with_multiple_definitions()
    logger.info(f'Deviations: {deviations}')
    
    collision_data = []
    for result in collisions:
        collision = result[0]
        collision_data.append({
            'definition_1': collision['definition_1'],
            'definition_2': collision['definition_2'],
            'id_1': collision['id_1'],
            'id_2': collision['id_2'],
        })

    deviation_data = []
    for result in deviations:
        deviation = result[0]
        deviation_data.append(deviation)

    context = {
        'collisions': collision_data,
        'duplicates': duplicates,
        'deviations': deviation_data
    }
    return render(request, 'admin/deconfliction_service/deconfliction_admin.html', context)

def resolve_duplicate(request, term_id, definition_id):
    try:
        cypher_query = """
        MATCH (t:NeoTerm)-[r:POINTS_TO]->(d:NeoDefinition)
        WHERE id(t) = $term_id AND id(d) = $definition_id
        DELETE r
        RETURN count(r) as deleted_relationships
        """
        results, _ = db.cypher_query(cypher_query, {
            'term_id': term_id, 
            'definition_id': definition_id
        })
        deleted_count = results[0][0]
        
        if deleted_count > 0:
            logger.info(f"Successfully removed relationship between term {term_id} and definition {definition_id}")
            messages.success(request, "Successfully resolved the duplicate relationship.")
        else:
            logger.warning(f"No relationship found between term {term_id} and definition {definition_id}")
            messages.warning(request, "No relationship found between this term and definition.")
            
        return redirect('admin:admin_deconfliction_view')
    except Exception as e:
        logger.error(f"Error resolving duplicate for term {term_id} and definition {definition_id}: {e}")
        messages.error(request, f"Error resolving duplicate: {str(e)}")
        return redirect('admin:admin_deconfliction_view')

def resolve_collision(request, definition_1, definition_2):
    try:
        logger.info(f"Resolving collision between definitions {definition_1} and {definition_2}")
        definition_node_1 = NeoDefinition.nodes.get_or_none(definition=definition_1)
        definition_node_2 = NeoDefinition.nodes.get_or_none(definition=definition_2)
        if definition_node_1 is None or definition_node_2 is None:
            logger.warning(f"Could not find definitions with definitions {definition_1} and {definition_2}")
            messages.warning(request, "Could not find definitions with these IDs.")
            return redirect('admin:admin_deconfliction_view')
        
        term_1 = definition_node_1.term.all()
        term_2 = definition_node_2.term.all()
        logger.info(term_1)
        logger.info(term_2)
        context = {
            'definition_1': definition_node_1,
            'definition_2': definition_node_2,
            'term_1': term_1,
            'term_2': term_2
        }
      
            
        return render(request,'admin/deconfliction_service/decollision.html', context)
        
    except Exception as e:
        logger.error(f"Error resolving collision between nodes {definition_1} and {definition_2}: {e}")
        messages.error(request, f"Error resolving collision: {str(e)}")
        return redirect('admin:admin_deconfliction_view')

def get_duplicate_definitions():
    """Find NeoDefinition nodes that have the same definition text"""
    cypher_query = """
    MATCH (d1:NeoDefinition)
    MATCH (d2:NeoDefinition)
    WHERE d1.definition = d2.definition 
    AND id(d1) < id(d2)  // This ensures we don't get reciprocal matches
    WITH d1.definition as definition_text, 
         collect(DISTINCT id(d1)) + collect(DISTINCT id(d2)) as definition_ids
    RETURN definition_text, definition_ids
    """
    results, _ = db.cypher_query(cypher_query)
    
    duplicates_data = []
    for definition_text, definition_ids in results:

        terms_query = """
        MATCH (t:NeoTerm)-[:POINTS_TO]->(d:NeoDefinition)
        WHERE id(d) IN $definition_ids
        RETURN t.text as term_text, id(t) as term_id, id(d) as definition_id
        """
        terms_results, _ = db.cypher_query(terms_query, {'definition_ids': definition_ids})
        
        terms_by_definition = {}
        for term_text, term_id, definition_id in terms_results:
            if definition_id not in terms_by_definition:
                terms_by_definition[definition_id] = []
            terms_by_definition[definition_id].append({
                'text': term_text,
                'id': term_id
            })
        
        duplicates_data.append({
            'definition_text': definition_text,
            'definition_ids': definition_ids,
            'terms_by_definition': terms_by_definition
        })
    
    return duplicates_data

def merge_duplicate_definitions(request, keep_id, remove_id):
    """Merge two duplicate definitions by redirecting all relationships to the kept definition"""
    try:
        merge_query = """
        // Get the definition we want to keep
        MATCH (keep:NeoDefinition)
        WHERE id(keep) = $keep_id
        
        // Get the definition we want to remove
        MATCH (remove:NeoDefinition)
        WHERE id(remove) = $remove_id
        
        // Find all terms pointing to the definition we want to remove
        OPTIONAL MATCH (t:NeoTerm)-[r:POINTS_TO]->(remove)
        
        // Create new relationships to the definition we're keeping
        WITH keep, remove, collect(t) as terms
        FOREACH (term IN terms | 
          MERGE (term)-[:POINTS_TO]->(keep)
        )
        
        // Delete the old node and all its relationships
        DETACH DELETE remove
        
        RETURN size(terms) as redirected_relationships
        """
        
        results, _ = db.cypher_query(merge_query, {
            'keep_id': keep_id,
            'remove_id': remove_id
        })
        
        redirected_count = results[0][0]
        logger.info(f"Successfully merged definitions. Redirected {redirected_count} relationships.")
        messages.success(request, f"Successfully merged definitions. Redirected {redirected_count} relationships.")
        
    except Exception as e:
        logger.error(f"Error merging definitions {keep_id} and {remove_id}: {e}")
        messages.error(request, f"Error merging definitions: {str(e)}")
    
    return redirect('admin:admin_deconfliction_view')

def admin_upgrade_definition(request, definition):

    try:
        logger.info('UPGRADING DEFINITION TO TERM')
        definition_node = NeoDefinition.nodes.get_or_none(definition=definition)
        if definition_node is None:
            logger.warning(f"Could not find definition with text {definition}")
            messages.warning(request, "Could not find definition with this text.")
            return redirect('admin:admin_deconfliction_view')
        
        logger.info(f"Upgrading definition '{definition}' to a term.")

        logger.info(f"Creating new term node.")
        
        term_node = NeoTerm.create_new_term()
        context_nodes = definition_node.context.all()

        for context_node in context_nodes:
            term_node.context.connect(context_node)
            context_node.term.connect(term_node)
        
        logger.info(term_node)

        alias_nodes = definition_node.collision_alias.all()

        for alias_node in alias_nodes:
            term_node.alias.connect(alias_node)
            alias_node.term.connect(term_node)
        
        term_node.definition.connect(definition_node)
        definition_node.term.connect(term_node)

        definition_node.collision_alias.disconnect_all()
        definition_node.collision.disconnect_all()
        
        logger.info(f"Successfully upgraded definition '{definition}' to a term.")
        messages.success(request, f"Definition successfully upgraded to a term.")
        return redirect('admin:admin_deconfliction_view')
    except Exception as e:
        logger.error(f"Error upgrading definition '{definition}': {e}")
        messages.error(request, "Error upgrading definition.")
        return redirect('admin:admin_deconfliction_view')