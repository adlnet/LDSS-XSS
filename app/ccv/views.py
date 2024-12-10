from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from django.conf import settings

IS_CCV = getattr(settings, 'IS_CCV', False)

# Create your views here.
class CCVDataIngest(APIView):
    def post(self, request):
        try:
            if not IS_CCV:
                return JsonResponse({'error': 'This is endpoint is not available on this instance.', 'status': 400})
            
            lcv_data = request.data.get('lcv_data')

            # write code that will validate the data contains values for these two fields format {'lcvid', 'definition'}
            if not validate_lcv_data(lcv_data):
                return JsonResponse({'error': 'Invalid data format'}, status=400)


            for term, definition in lcv_data:
                pass
            return JsonResponse({'message': 'Data successfully ingested'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def validate_lcv_data(lcv_data):
    # This is a placeholder for the validation logic
    

    return False
        
    