from deconfliction_service.views import run_deconfliction
from django.http import JsonResponse

import logging
logger=logging.getLogger('dict_config_logger')
def run_ccv_node_creation(definition, lcvid, lcvid_parent_string):

    try:
        logger.info('Running Deconfliction')
        logger.info(f"Definition:{definition} ")
        result = run_deconfliction(definition)
        logger.info(result)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)