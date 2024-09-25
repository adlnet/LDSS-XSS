from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from uuid import uuid5, NAMESPACE_URL
import json
from neomodel import db
from .models import CounterNode, UIDNode


MAX_CHILDREN = 2**32 -1

# Create your views here.
def generate_uid_node(request: HttpRequest):

    request_body = json.loads(request.body)
    print(request_body)
    strict_parent_validation = request_body.get('strict_parent_validation', False)
    parent_uid = request_body.get('parent_uid', None)
    namespace = request_body.get('namespace', 'LCV') #??? Ask Hunter about where namespace is actually configured and is it different than just organization?
    parent_node = UIDNode.get_node_by_uid(parent_uid)

    if parent_node is None:
        if strict_parent_validation:
            return HttpResponse("{ 'error': 'Parent node not found' }", status=404, content_type='application/json')
        else:
            parent_node = UIDNode.create_node(uid = parent_uid, namespace = namespace)
    
    num_children = parent_node.children.count()

    if num_children > MAX_CHILDREN:
        return HttpResponse("{ 'error': 'Max children exceeded for {parent_uid}' }", status=400, content_type='application/json')
    local_uid = CounterNode.increment().counter

    new_child_node = UIDNode.create_node(uid = local_uid, namespace = namespace)

    parent_node.children.connect(new_child_node)

    return HttpResponse("{ 'uid': '" + str(local_uid) + "' }", content_type='application/json')