import logging
import json
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests.exceptions import HTTPError
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

import requests


from api.serializers import (TermJSONLDSerializer, TermSetJSONLDSerializer,
                             TermSetSerializer)
from core.management.utils.xss_helper import sort_version
from core.models import  NeoTerm, TermSet

from .utils import create_terms_from_csv, validate_csv, convert_to_xml

import pandas as pd

logger = logging.getLogger('dict_config_logger')


def check_status(messages, queryset):
    queryset = queryset.filter(status='published')
    if not queryset:
        message = "Error fetching record, no published record with required parameters"
        messages.append(message)
        logger.error(message)
        raise ObjectDoesNotExist()
    
    return queryset


class JSONLDRenderer(JSONRenderer):
    """Renderer restricted to JSON-LD"""
    media_type = 'application/ld+json'
    format = 'jsonld'


class JSONLDDataView(RetrieveAPIView):
    """Handles HTTP requests to for JSON-LD schemas"""
    renderer_classes = [JSONLDRenderer, *api_settings.DEFAULT_RENDERER_CLASSES]

    def get_queryset(self):
        """
        Determines if the requested object is a Term or TermSet and returns
        the queryset
        """
        # Due to the IRI a term has a '?' so check for a param without a value
        if self.request.query_params:
            for _, v in self.request.query_params.items():
                if len(v) == 0:
                    return Term.objects.all().filter(status='published')
        
        return TermSet.objects.all().filter(status='published')

    def get_serializer_class(self):
        """
        Determines if the requested object is a Term or TermSet and returns
        the serializer
        """
        # Due to the IRI a term has a '?' so check for a param without a value
        if self.request.query_params:
            for _, v in self.request.query_params.items():
                if len(v) == 0:
                    return TermSetJSONLDSerializer
        
        return TermJSONLDSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Return a JSON-LD representation of the requested object
        """
        # Due to the IRI a term has a '?' so check for a param without a value
        if self.request.query_params:
            for k, v in self.request.query_params.items():
                if len(v) == 0:
                    self.kwargs['pk'] = self.kwargs['pk'] + '?' + k
                    break
        
        # get the specific object and serializer
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # generated JSON-LD is stored as a python dict labeled 'graph'
        ld_dict = serializer.data['graph']
        
        # build the external URL to this API and add it to the context
        ldss = request.build_absolute_uri(
            reverse('api:json-ld', args=[1]))[:-1]
        
        if hasattr(settings, 'BAD_HOST') and hasattr(settings, 'OVERIDE_HOST'):
            ldss = ldss.replace(settings.BAD_HOST, settings.OVERIDE_HOST)
        
        ld_dict['@context']['ldss'] = ldss
        
        return Response(ld_dict)


class SchemaLedgerDataView(GenericAPIView):
    """Handles HTTP requests to the Schema Ledger"""

    queryset = TermSet.objects.all().filter(status='published')

    def get(self, request):
        """This method defines the API's to retrieve data
        from the Schema Ledger"""

        queryset = self.get_queryset()

        # all requests must provide the schema name
        messages = []
        name = request.GET.get('name')
        version = request.GET.get('version')
        iri = request.GET.get('iri')

        errorMsg = {
            "message": messages
        }

        if name:
            # look for a model with the provided name
            queryset = queryset.filter(name=name)

            if not queryset:
                messages.append(f"Error; no schema found with the name '{name}'")
                errorMsg = {
                    "message": messages
                }
                return Response(errorMsg, status.HTTP_400_BAD_REQUEST)

            # if the schema name is found, filter for the version.
            # If no version is provided, we fetch the latest version
            if not version:
                queryset = [ts for ts in queryset]
                queryset = sort_version(queryset, reverse_order=True)
            
            else:
                queryset = queryset.filter(version=version)

            if not queryset:
                messages.append(f"Error; no schema found for version '{version}'")
                errorMsg = {
                    "message": messages
                }
                
                return Response(errorMsg, status.HTTP_400_BAD_REQUEST)
        
        elif iri:
            # look for a model with the provided name
            queryset = queryset.filter(iri=iri)

            if not queryset:
                messages.append(f"Error; no schema found with the iri '{iri}'")
                errorMsg = {
                    "message": messages
                }
                
                return Response(errorMsg, status.HTTP_400_BAD_REQUEST)
        
        else:
            messages.append("Error; query parameter 'name' or 'iri' is required")
            logger.error(messages)
            
            return Response(errorMsg, status.HTTP_400_BAD_REQUEST)
        
        try:
            # only way messages gets sent is if there was
            # an error serializing or in the response process.
            messages.append(
                "Error fetching records please check the logs.")
            
            return self.handle_response(queryset)
        
        except ObjectDoesNotExist:
            errorMsg = {
                "message": messages
            }
            
            return Response(errorMsg, status.HTTP_400_BAD_REQUEST)
        
        except HTTPError as http_err:
            logger.error(http_err) 
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as err:
            logger.error(err)
            return Response(errorMsg, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_response(self, queryset):
        serializer_class = TermSetSerializer(queryset[0])
        logger.info(queryset[0])
        # could be used to add link header if needed
        # if 'format' in request.query_params:
        #     link = '<%s>;' % request.get_full_path().replace(
        #         request.query_params.get('format'), 'jsonld')
        # else:
        #     link = f'<{request.get_full_path()}>;'
        # link += ' rel="alternate"; type="application/ld+json"'
        
        return Response(serializer_class.data, status.HTTP_200_OK)


class TransformationLedgerDataView(GenericAPIView):
    """Handles HTTP requests to the Transformation Ledger"""
    queryset = TermSet.objects.all().filter(status='published')

    def get(self, request):
        """This method defines the API's to retrieve data
        from the Transformation Ledger"""
        # all requests must provide the source and target
        # schema names and versions
        source_name = request.GET.get('sourceName')
        source_iri = request.GET.get('sourceIRI')
        target_name = request.GET.get('targetName')
        target_iri = request.GET.get('targetIRI')
        source_version = request.GET.get('sourceVersion')
        target_version = request.GET.get('targetVersion')

        messages = self._check_params(
            source_name, source_iri, target_name, target_iri)

        errorMsg = {
            "message": messages
        }

        if len(messages) == 0:
            # look for a model with the provided name

            try:
                source_qs = self._filter_by_source(source_name, source_version, source_iri, messages)
                target_qs = self._filter_by_target(target_name, target_version, target_iri, messages)
                mapping_dict = target_qs.first().mapped_to(source_qs.first().iri)
                messages.append("Error fetching records please check the logs.")
            except ObjectDoesNotExist:
                errorMsg = {
                    "message": messages
                }
                return Response(errorMsg, status.HTTP_400_BAD_REQUEST)
            except HTTPError as http_err:
                logger.error(http_err)
                return Response(errorMsg,
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as err:
                logger.error(err)
                return Response(errorMsg,
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response(
                    {
                        'source': source_qs.first().iri,
                        'target': target_qs.first().iri,
                        'schema_mapping': mapping_dict
                    }, status.HTTP_200_OK)
        else:
            logger.error(messages)
            return Response(errorMsg, status.HTTP_400_BAD_REQUEST)

    def _check_params(self, source_name, source_iri, target_name, target_iri):
        messages = []
        if source_name == source_iri and source_name is None:
            messages.append("Error; query parameter 'sourceName' or 'sourceIRI' is required")

        if target_name == target_iri and target_name is None:
            messages.append("Error; query parameter 'targetName' or 'targetIRI' is required")
        
        return messages

    def _filter_by_source(self, source_name, source_version, source_iri,
                          messages):
        if source_name:
            # look for a model with the provided name
            queryset = self.get_queryset().filter(name=source_name)
            if not queryset:
                messages.append(f"Error; no source schema found with the name '{source_name}'")
                raise ObjectDoesNotExist()

            # if the schema name is found, filter for the version.
            # If no version is provided, we fetch the latest version
            if not source_version:
                term_sets = [ts for ts in queryset]
                term_set = sort_version(term_sets, reverse_order=True)[0]
                queryset = queryset.filter(iri=term_set.iri)
            
            else:
                queryset = queryset.filter(version=source_version)
            
            if not queryset:
                messages.append(f"Error; no source schema found for version '{source_version}'")
                raise ObjectDoesNotExist()
        
        elif source_iri:
            # look for a model with the provided iri
            queryset = self.get_queryset().filter(iri=source_iri)

            if not queryset:
                messages.append(f"Error; no schema found with the iri '{source_iri}'")
                raise ObjectDoesNotExist()
        
        return queryset

    def _filter_by_target(self, target_name, target_version, target_iri,
                          messages):
        queryset = self.get_queryset()
        if target_name:
            # look for a model with the provided name
            queryset = queryset.filter(name=target_name)

            if not queryset:
                messages. \
                    append(f"Error; no target schema found {target_name}'")
                raise ObjectDoesNotExist()

            # if the schema name is found, filter for the version.
            # If no version is provided, we fetch the latest version
            if not target_version:
                term_sets = [ts for ts in queryset]
                term_set = sort_version(term_sets, reverse_order=True)[0]
                queryset = queryset.filter(iri=term_set.iri)
            else:
                queryset = queryset.filter(version=target_version)

            if not queryset:
                messages.append(f"Error; no target schema found for version '{target_version}'")
                raise ObjectDoesNotExist()

        elif target_iri:
            # look for a model with the provided name
            queryset = queryset.filter(iri=target_iri)

            if not queryset:
                messages.append(f"Error; no schema found '{target_iri}'")
                raise ObjectDoesNotExist()
        
        return queryset


class ImportCSVView(APIView):
    permission_classes = [AllowAny]
    required_columns = ['Term', 'Definition', 'Context', 'Context Description']
    @csrf_exempt
    def post(self, request: HttpRequest):
        try:
            csv_file = request.FILES.get('file')  # Assuming the file is sent with key 'file'
            if not csv_file:
                return JsonResponse({'error': 'No file provided.'}, status=400)
            
            validation_result = validate_csv(csv_file)
            if validation_result['error']:
                return JsonResponse(validation_result, status=400)
            
            create_terms_from_csv(validation_result['data_frame'])
            logger.info('CSV file uploaded successfully')
            
            return JsonResponse({'message': 'CSV file is valid'}, status=200)
        
        except Exception as e:
            logger.error(f'Error uploading CSV file: {str(e)}')
            return JsonResponse({'error': 'Internal Server error'}, status=500)
        
class ExportTermsView(APIView):
    permission_classes = [AllowAny]
    @csrf_exempt
    def get(self, request: HttpRequest):
        try: 

            terms = NeoTerm.nodes.all()

            terms_data = [{
                       "term": term.term, 
                       "definition": term.definition, 
                       "context": term.context, 
                       "context_description": term.context_description} 
                       for term in terms
                       ]
            
            if request.data.get('format') == 'xml':
                logger.info('Exporting terms to XML')
                return convert_to_xml(terms_data)
                 
            logger.info('Exporting terms to JSON')
            return JsonResponse({'terms': terms_data}, status=200)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

## Classes for connecting to external APIS.
## Param - APIVIEW is a django rest framework class that helps with API, with built in methods like get, post, put, delete
## Post to send requested terms. - the requested terms will be in the post body, so we will need to parse that and search for the terms
class SendTermsToExternalAPI(APIView):
    logger.debug("Hit the SendTermsToExternalAPI view POST method")  # Simple check
    ## Allow any lets ANY user, including unauth access this API endpoint. Do we want to make more restrictive in prod? - MB
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Extract the external API credentials and endpoint from the request (the endpoint to send the data)
        api_url = request.data.get('url')  # URL to connect to
        api_endpoint = request.data.get('endpoint')  # The specific API endpoint
        username = request.data.get('username')
        password = request.data.get('password')
        requested_terms = request.data.get('terms') # The terms requested by the external API


        #what is api_url and others here?
        #logger.debug(" api_url is ", api_url)
        #logger.debug("api endpoint is ", api_endpoint)
        #logger.debug('username is ', username)
        #logger.debug('password is ' ,password)
        
        if not api_url or not api_endpoint:
            return JsonResponse({'error': 'Failed to parse URL or endpoint: missing required parameters.'}, status=400)

        # Fetch terms 
        terms = NeoTerm.nodes.all()  
        ## This is an example framework, I need to implement a search here, for the users query. So, maybe parse the post for what they want
        ## then search and return it?
        
   
        search_term = request.data.get('search_term', '')
        if search_term:
            terms = NeoTerm.nodes.filter(term__icontains=search_term)
            
        else:
            terms = NeoTerm.nodes.all()


        terms_data = [
            {
                "term": term.term,
                "definition": term.definition,
                "context": term.context,
                "context_description": term.context_description
            }
            for term in terms
        ]
    
        ## Also we will need to to send a success response for if there is no term but the request was successful. - MB
        ## Maybe something like if terms_data is empty then response = {'message': 'No terms to send'}
        if not terms_data:
            return JsonResponse({'message': 'No terms found to send'}, status=200)
        else:
            # Convert the terms to JSON (or use CSV if needed)
            # Sending JSON data to the external API
            headers = {'Content-Type': 'application/json'}
            data = {'terms': terms_data}
        
        # Authenticate (Basic Authentication or using credentials)
        auth = (username, password)
        #test
        #api_url = 'http://openlxp-xss-2:8030'
        try:
            # Send data to the external API via POST request
            response = requests.post(f'{api_url}/{api_endpoint}', json=data, headers=headers, auth=auth)
            #response = requests.post(f'http://openlxp-xss-2:8030/send-terms/', json=data, headers=headers, auth=auth)

            if response.status_code == 200:
                return JsonResponse({'message': 'Terms sent successfully to external API2'}, status=200)
            else:
                return JsonResponse({'error': f'Failed to send terms: {response.text}'}, status=response.status_code)
        
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'Error connecting to external API: {str(e)}'}, status=500)

## Param - APIVIEW is a django rest framework class that helps with API, with built in methods like get, post, put, delete
## Get to receive terms requested from external API.
class RequestTermsFromExternalAPI(APIView):
    
    logger.debug("Hit the RequestTermsFromExternalAPI view POST method")  # Simple check
    ## Allow any lets ANY user, including unauth access this API endpoint. Do we want to make more restrictive in prod? - MB
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        logger.debug(f"Raw request data: {request.body.decode('utf-8')}")  # Log the raw request body
        try:
            data = json.loads(request.body.decode('utf-8'))  # Manually parse JSON if necessary
            logger.debug(f"Parsed request data: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        # Extract the data sent in the request body (this will be a JSON payload)
        data = request.data
  
        logger.debug(f"Received request data: {data}")  # Add a log to check the incoming data

        api_url = data.get('url')  # URL to connect to the external API
        api_endpoint = data.get('endpoint')  # Specific endpoint for the API
        username = data.get('username')  # Username for basic authenticatiofn
        password = data.get('password')  # Password for basic authentication
        search_term = data.get('search_term')  # Search term to filter the terms (if provided)
        ## Example search terms. Do we know all of the params for querry required yet? 
        ## date_created = data.get('date_created')  # Start date for filtering
        ## date_until = data.get('date_until')  # End date for filtering

   # Print debug info
        logger.debug(f"Searching for terms with the search keyword: {search_term}")
            # Optional: Log the parameters to debug
        logger.debug(f"API URL: {api_url}")
        logger.debug(f"API Endpoint: {api_endpoint}")
        logger.debug(f"Username: {username}")
        logger.debug(f"Password: {password}")
        logger.debug(f"Search term: {search_term}")
    
  # Check if the essential parameters are provided
        if not api_url or not api_endpoint:
            logger.debug(f"API URL: {api_url}")
            logger.debug(f"API Endpoint: {api_endpoint}")
            return JsonResponse({'error': 'API URL or endpoint missing'}, status=400)
        
        # Authentication (basic authentication or API token)
        auth = (username, password) if username and password else None

####
        try:
            # Send the GET request to the external API
            response = requests.post(f"{api_url}/{api_endpoint}", json=data, auth=auth)
            
            if response.status_code == 200:
                terms_data = response.json()  # Assuming the API returns JSON data
                
                # Here, we save the terms or process them
                for term in terms_data.get('terms', []):
                    NeoTerm(
                        term=term['term'],
                        definition=term['definition'],
                        context=term['context'],
                        context_description=term['context_description']
                    ).save()
                
                return JsonResponse({'message': 'Terms received and saved successfully'}, status=200)
            else:
                #This si the problem, the response is not 200, so we need to handle this. - MB
                return JsonResponse({'error': f"Failed to fetch terms: {response.text}"}, status=response.status_code)
        
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f"Error connecting to the external API: {str(e)}"}, status=500)
#####
#

            
