from django.shortcuts import render

from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from typing import List
from uuid import uuid4

logger = logging.getLogger('dict_config_logger')


def run_deconfliction(definition, es_client):
    try:
        es_client.ensure_index()
        definition_embedding  = es_client.create_embedding(definition)
        response = es_client.check_similarity(definition_embedding)
        response['definition_embedding'] = definition_embedding
        return response
    except Exception as e:
        logger.error(f"Error in run_deconfliction: {e}")
        raise e

    

