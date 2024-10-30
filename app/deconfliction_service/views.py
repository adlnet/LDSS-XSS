from django.shortcuts import render

from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from typing import List
from uuid import uuid4

from .node_utils import create_vector_index, find_similar_text_by_embedding, generate_embedding, evaluate_deconfliction_status

logger = logging.getLogger('dict_config_logger')


def run_deconfliction(alias: str, definition: str, context: str, context_description: str):
    try:
        logger.info('Running Deconfliction')
        definition_vector_embedding = generate_embedding(definition)
        create_vector_index('definitions', 'NeoDefinition', 'embedding')
        most_similar_text = find_similar_text_by_embedding(definition_vector_embedding, 'definition', 'definitions')
        deconfliction_status = evaluate_deconfliction_status(most_similar_text)
        return definition_vector_embedding, deconfliction_status
    except Exception as e:
        logger.error(f"Error in run_deconfliction: {e}")
        raise e