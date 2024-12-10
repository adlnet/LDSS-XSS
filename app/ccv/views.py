from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.conf import settings
import json
from .utils import run_ccv_node_creation
IS_CCV = getattr(settings, 'IS_CCV', False)
import logging

logger = logging.getLogger('dict_config_logger')
# Create your views here.
class CCVDataIngest(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            if not IS_CCV:
                return JsonResponse({'error': 'This is endpoint is not available on this instance.'}, status=400)
            
            data = json.loads(request.body)
            logger.info(data)
            for item in data:
                definition = item.get('definition')
                lcvid = item.get('lcvid')
                parent_id = item.get('parent_id')
                logger.info(definition)
                logger.info(lcvid)
                logger.info(parent_id)
                run_ccv_node_creation(definition, lcvid, parent_id)
            # logger.info(data)
            # for obj in data:
            #     lcvid = obj.get('lcvid')
            #     definition = obj.get('definition')
            #     parent_id = obj.get('parent_id')

            #     if not all([lcvid, parent_id, definition]):
            #         return JsonResponse({'error': 'Invalid JSON format'}, status=400)
                
            #     run_ccv_node_creation(definition, lcvid, parent_id)
                

            # for term, definition in lcv_data:
            #     pass
            return JsonResponse({'message': 'Data successfully ingested'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def validate_lcv_data(lcv_data):
    # This is a placeholder for the validation logic
    

    return False
        
    