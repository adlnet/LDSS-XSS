from django.shortcuts import render

from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from typing import List

logger = logging.getLogger('dict_config_logger')
model = SentenceTransformer('all-mpnet-base-v2')

from .utils import ElasticsearchClient

# def single_term_comparision(term: str, definition: str):
#     # does a duplicate exist? does
#     try:
#         definition_vector= model.encode(definition, convert_to_numpy=True)
#         normalized_definition_vector = normalize_vector(definition_vector)
#         #es_index that stores normalized definition vector then we check if there is a similar vector in the index and then if there is then we know we have a duplicate based on score or we have a deviation based on score
#         logger.info(f"Normalized definition vector: {normalized_definition_vector}")

#         #getting all term nodes from neo4j and then turning them into vectors and storing them temporarily?
        
#         #as nodes are added, store them in neo4j but also as vectors in elasticsearch if so how do we tie that vector to a neo4j UID
#     except Exception as e:
#         logger.error(f"Error in single_term_comparision: {e}")



# def normalize_vector(vector):
#     return vector / np.linalg.norm(vector)

# def search_similar_vectors(query_vector, index='openlxp_xss_index'):
#     pass


def run_deconfliction(terms: List[str]):

    try:
        es = ElasticsearchClient()
        es.connect()
        es.ensure_index()
        #get all terms from neo4j
        #for term in terms:
        #   single_term_comparision(term)
        for term in terms:
            definition_embedding, term_embedding  = es.create_embedding(term)
            es.check_similarity(term, embeddings)
            es.index_document(term, embeddings)
    except Exception as e:
        logger.error(f"Error in run_deconfliction: {e}")
    finally:
        if es is not None:
            es.disconnect()

    

