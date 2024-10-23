from django.shortcuts import render

from sentence_transformers import SentenceTransformer
import numpy as np
import logging

from .utils import get_elastic_search_connection

logger = logging.getLogger('dict_config_logger')
model = SentenceTransformer('all-mpnet-base-v2')

def single_term_comparision(term: str, definition: str):
    # does a duplicate exist? does
    try:
        definition_vector= model.encode(definition, convert_to_numpy=True)
        normalized_definition_vector = normalize_vector(definition_vector)
        #es_index that stores normalized definition vector then we check if there is a similar vector in the index and then if there is then we know we have a duplicate based on score or we have a deviation based on score
        logger.info(f"Normalized definition vector: {normalized_definition_vector}")

        es = get_elastic_search_connection()

        



        #getting all term nodes from neo4j and then turning them into vectors and storing them temporarily?
        
        #as nodes are added, store them in neo4j but also as vectors in elasticsearch if so how do we tie that vector to a neo4j UID
    except Exception as e:
        logger.error(f"Error in single_term_comparision: {e}")



def normalize_vector(vector):
    return vector / np.linalg.norm(vector)


