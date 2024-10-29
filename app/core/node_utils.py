from typing import Type, Any
from django_neomodel import DjangoNode
from neomodel import db
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
import logging

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

# TODO: Deprecate this when we figure out the Cypher query approach
def has_semantically_similar_value(node_class: Type[DjangoNode], input_sentence: str, similarity_threshold: float = 0.8) -> bool:
    """
    Check if any instance of node_class exists with a semantic similarity to the input sentence.

    :param node_class: The DjangoNode class to check against.
    :param input_sentence: The sentence to compare against existing node definitions.
    :param similarity_threshold: The minimum cosine similarity for a match.
    :return: True if any matching instance exists, False otherwise.
    """
    # Get all existing definitions as sentences
    existing_sentences = [node.definition for node in node_class.nodes.all()]  # Adjust according to your model

    # Compute the embedding for the input sentence
    input_embedding = model.encode(input_sentence, convert_to_tensor=True)

    # Compute embeddings for existing sentences
    existing_embeddings = model.encode(existing_sentences, convert_to_tensor=True)

    # Compute cosine similarities
    cosine_scores = util.pytorch_cos_sim(input_embedding, existing_embeddings)
    logger.info(f"Similarity scores: {cosine_scores}")

    # Check if any cosine score exceeds the similarity threshold
    if torch.any(cosine_scores >= similarity_threshold):
        return True

    return False

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