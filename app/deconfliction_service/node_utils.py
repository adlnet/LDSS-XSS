from typing import Type, Any
from django_neomodel import DjangoNode
from neomodel import db
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
import logging
from core.constants import MODEL_VECTOR_DIMENSION

logger = logging.getLogger('dict_config_logger')

model = SentenceTransformer('all-MiniLM-L6-v2')

def is_any_node_present(node_class: Type[DjangoNode], **filters: Any) -> bool:
    """
    Check if any instance of node_class exists with the given filters.

    :param node_class: The DjangoNode class to check against.
    :param filters: Keyword arguments for filtering the node instances.
    :return: True if any matching instance exists, False otherwise.
    """
    node_set = node_class.nodes.filter(**filters)
    return len(node_set) > 0

def generate_embedding(text: str) -> list:
    """
    Generate a sentence embedding for the given text.

    :param text: The text to generate an embedding for.
    :return: The sentence embedding as a numpy array.
    """
    logger.info(len(model.encode(text).tolist()))
    return model.encode(text).tolist()

def get_terms_with_multiple_definitions():
    cypher_query = """
    MATCH (t:NeoTerm)-[:POINTS_TO]->(d:NeoDefinition)
    WITH t, COUNT(d) AS definition_count
    WHERE definition_count > 1
    RETURN t, definition_count
    """
    results, _ = db.cypher_query(cypher_query)

    logger.info(f"Results: {results}")
    
    # terms = []
    # for record in results:
    #     term_node = NeoTerm.inflate(record[0])
    #     terms.append((term_node, record[1]))  # Append the term and its definition count
    
    # return terms

def show_current_vector_indeces():
    cypher_query = """
    SHOW INDEXES WHERE type = "VECTOR"
    """

    logger.info(f"Current vector indeces: {db.cypher_query(cypher_query)}")

def create_vector_index(index_name, node_name, embedding_field_name='embedding'):
    cypher_query = f"""
    CREATE VECTOR INDEX `{index_name}` IF NOT EXISTS
    FOR (n:{node_name})
    ON (n.{embedding_field_name})
    OPTIONS {{
        indexConfig: {{
            `vector.dimensions`: {MODEL_VECTOR_DIMENSION},
            `vector.similarity_function`: 'cosine'
        }}
    }}
    """

    logger.info("Cypher query: " + cypher_query)

    results, _ = db.cypher_query(cypher_query)
    show_current_vector_indeces()
    return results

def find_similar_text_by_embedding(input_embedding, return_field_name, index_name, top_k_results=6):
    cypher_query = f"""
        CALL db.index.vector.queryNodes('{index_name}', {top_k_results}, {input_embedding})
        YIELD node, score
        RETURN node.{return_field_name}, score
    """

    results, _ = db.cypher_query(cypher_query)
    logger.info(f"Similarity results successful. Most similar items: {results}")
    return results

def find_similar_text_by_node_field(node_name, field_name, return_field_name, index_name, top_k_results=6):
    cypher_query = f"""
        MATCH (n:{node_name})
        CALL db.index.vector.queryNodes('{index_name}', {top_k_results}, n.{field_name})
        YIELD node, score
        RETURN node.{return_field_name}, score
    """

    results, _ = db.cypher_query(cypher_query)
    logger.info(f"Similarity results successful. Most similar items: {results}")
    return results