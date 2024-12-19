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
            logger.info('CCVDataIngest')
            if not IS_CCV:
                return JsonResponse({'error': 'This is endpoint is not available on this instance.'}, status=400)
            
            data = json.loads(request.body)
            logger.info(data)
            
            definition = data.get('definition')
            lcvid = data.get('lcvid')
            parent_id = data.get('uid_chain')
            
            run_ccv_node_creation(definition, lcvid, parent_id)
            return JsonResponse({'message': 'Data successfully ingested'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def validate_lcv_data(lcv_data):
    # This is a placeholder for the validation logic
    

    return False
        
    