from deconfliction_service.views import run_deconfliction
from django.http import JsonResponse
from deconfliction_service.node_utils import generate_embedding, create_vector_index, find_similar_text_by_embedding
from .models import CCVTerm


import logging
logger=logging.getLogger('dict_config_logger')
def run_ccv_node_creation(definition, lcvid, lcvid_parent_string):

    try:
        logger.info('Running Deconfliction')
        logger.info(f"Definition:{definition} ")
        match = match_definition(definition)
        if not match:
            logger.info(f'No match found for LCV Term{lcvid_parent_string}. Creating a new ccv term.')
            ccv_node = CCVTerm.create_node(definition, lcvid, lcvid_parent_string)


    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
def match_definition(definition):
    try:
        logger.info(f'Matching {definition} with existing definitions')

        definition_vector_embedding = generate_embedding(definition)
        create_vector_index('definitions', 'NeoDefinition', 'embedding')
        results = find_similar_text_by_embedding(definition_vector_embedding, 'definition', 'definitions')
        if results:
            return results
        else:
            return None
    except Exception as e:
        logger.error(f'Error matching definition: {e}')