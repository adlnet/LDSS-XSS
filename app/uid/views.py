from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
#from uuid import uuid5, NAMESPACE_URL
import json
import logging
from neomodel import db
from .models import CounterNode, Provider, LCVTerm, LanguageSet
from .models import UIDGenerator, UIDNode
from .forms import ProviderForm, LCVTermForm
#from .utils import generate_uid # import generate_uid 

# Set up logging to capture errors and important information
logger = logging.getLogger(__name__)

# Attempt to initialize the UID generator
try:
    uid_generator = UIDGenerator()
except RuntimeError as e:
    # Log an error if UIDGenerator fails to initialize (e.g., due to Neo4j connection issues)
    logger.error(f"Failed to initialize UIDGenerator: {e}")
    uid_generator = None  # Handle initialization failure appropriately

MAX_CHILDREN = 2**32 -1

# Initialzie the UID generator
#uid_generator = UIDGenerator()

# Create your views here.
def generate_uid_node(request: HttpRequest):
    request_body = json.loads(request.body)
    print(request_body)
    strict_parent_validation = request_body.get('strict_parent_validation', False)
    parent_uid = request_body.get('parent_uid', None)
    namespace = request_body.get('namespace', 'LCV') #??? Ask Hunter about where namespace is actually configured and is it different than just organization?
    parent_node = UIDNode.get_node_by_uid(parent_uid, namespace) #added namespace

    if parent_node is None:
        if strict_parent_validation:
            return HttpResponse("{ 'error': 'Parent node not found' }", status=404, content_type='application/json')
        else:
            parent_node = UIDNode.create_node(uid = parent_uid, namespace = namespace)
    
    #num_children = parent_node.children.count()

    # Count children using a loop
    num_children = 0
    for child in parent_node.children:
        num_children += 1

    if num_children > MAX_CHILDREN:
        return HttpResponse("{ 'error': 'Max children exceeded for {parent_uid}' }", status=400, content_type='application/json')
    local_uid = uid_generator.generate_uid() # updated to use new UID Generation method
    #local_uid = CounterNode.increment().counter

    new_child_node = UIDNode.create_node(uid = local_uid, namespace = namespace)

    parent_node.children.connect(new_child_node)

    return HttpResponse("{ 'uid': '" + str(local_uid) + "' }", content_type='application/json')

#Potential code to retrieve parent and child nodes using the upstream and downstream capabilities
#def get_upstream_providers(request, uid):
    #try:
      #  lcv_term = LCVTerm.nodes.get(uid=uid)
     #   upstream_providers = lcv_term.get_upstream()
    #    upstream_uids = [p.uid for p in upstream_providers]
   #     return JsonResponse({'upstream_uids': upstream_uids})
  #  except LCVTerm.DoesNotExist:
 #       return JsonResponse({'error': 'LCVTerm not found'}, status=404)

#def get_downstream_lcv_terms(request, uid):
    #try:
        #provider = Provider.nodes.get(uid=uid)
       # downstream_lcv_terms = provider.get_downstream()
      #  downstream_uids = [l.uid for l in downstream_lcv_terms]
     #   return JsonResponse({'downstream_uids': downstream_uids})
    #except Provider.DoesNotExist:
    #    return JsonResponse({'error': 'Provider not found'}, status=404)

# Provider and LCVTerm (Otherwise alternative Parent and child)
def create_provider(request):
    if request.method == 'POST':
        form = ProviderForm(request.POST)
        if form.is_valid():
            provider = form.save()
            provider.uid = uid_generator.generate_uid()  # Ensure UID is generated
            provider.save()
            #form.save()
            return redirect('uid:success')
    else:
        form = ProviderForm()
    return render(request, 'create_provider.html', {'form': form})

def create_lcvterm(request):
    if request.method == 'POST':
        form = LCVTermForm(request.POST)
        if form.is_valid():
            lcvterm = form.save()
            lcvterm.uid = uid_generator.generate_uid()  # Ensure UID is generated
            lcvterm.save()
            #form.save()
            return redirect('uid:success')
    else:
        form = LCVTermForm()
    return render(request, 'create_lcvterm.html', {'form': form})

def success_view(request):
    return render(request, 'success.html', {'message': 'Operation completed successfully!'})

# Postman view
def export_to_postman(request, uid):
    try:
        provider = Provider.objects.get(uid=uid)
        data = {
            'name': provider.name,
            'uid': provider.uid,
            # Add other fields you want to export
        }
    except Provider.DoesNotExist:
        try:
            lcv_term = LCVTerm.objects.get(uid=uid)
            data = {
                'name': lcv_term.name,
                'uid': lcv_term.uid,
                # Add other fields you want to export
            }
        except LCVTerm.DoesNotExist:
            try:
                with db.transaction:
                    #language_set = LanguageSet.objects.get(uid=uid)
                    language_set = LanguageSet.nodes.get(uid=uid)
                    data = {
                        'name': language_set.name,
                        'uid': language_set.uid,
                        'terms': [term.uid for term in language_set.terms], # this should update Postman on LanguageSet changes to a Node.
                        #'terms': [term.uid for term in language_set.terms.all()],
                }
            except LanguageSet.DoesNotExist:
                return JsonResponse({'error': 'UID not found'}, status=404)

    return JsonResponse(data)
