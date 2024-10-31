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

from .node_utils import create_vector_index, find_colliding_definition_nodes, find_similar_text_by_embedding, generate_embedding, evaluate_deconfliction_status

logger = logging.getLogger('dict_config_logger')


def run_deconfliction(alias: str, definition: str, context: str, context_description: str):
    try:
        logger.info('Running Deconfliction')
        definition_vector_embedding = generate_embedding(definition)
        create_vector_index('definitions', 'NeoDefinition', 'embedding')
        results = find_similar_text_by_embedding(definition_vector_embedding, 'definition', 'definitions')
        deconfliction_status, most_similar_text = evaluate_deconfliction_status(results)
        if deconfliction_status == 'unique':
            return definition_vector_embedding, deconfliction_status, None
        return definition_vector_embedding, deconfliction_status, most_similar_text
    except Exception as e:
        logger.error(f"Error in run_deconfliction: {e}")
        raise e
    
def deconfliction_admin_view(request):
    collisions = find_colliding_definition_nodes()
    logger.info(f"Collisions: {collisions}")
    
    collision_data = []
    for result in collisions:
        collision = result[0]  
        collision_data.append({
            'definition_1': collision['definition_1'],
            'definition_2': collision['definition_2'],
            'id_1': collision['id_1'],
            'id_2': collision['id_2'],
        })
    
    context = {
        'collisions': collision_data,
        'deviations': [],
        'duplicates': [],
    }
    
    return render(request, 'admin/deconfliction_service/deconfliction_admin.html', context)

def resolve_collision(request, id_1, id_2):
    try:
        cypher_query = """
        MATCH (n:NeoDefinition)-[r:IS_COLLIDING_WITH]-(m:NeoDefinition)
        WHERE id(n) = $id_1 AND id(m) = $id_2
        DELETE r
        RETURN count(r) as deleted_relationships
        """
        
        results, _ = db.cypher_query(cypher_query, {'id_1': id_1, 'id_2': id_2})
        deleted_count = results[0][0]
        
        if deleted_count > 0:
            logger.info(f"Successfully removed collision relationship between nodes {id_1} and {id_2}")
            messages.success(request, "Successfully resolved the collision.")
        else:
            logger.warning(f"No collision relationship found between nodes {id_1} and {id_2}")
            messages.warning(request, "No collision relationship found between these definitions.")
            
        return redirect('admin:admin_deconfliction_view')
        
    except Exception as e:
        logger.error(f"Error resolving collision between nodes {id_1} and {id_2}: {e}")
        messages.error(request, f"Error resolving collision: {str(e)}")
        return redirect('admin:admin_deconfliction_view')
