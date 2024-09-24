from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from uuid import uuid5, NAMESPACE_URL
import json
from neomodel import db
from .models import CounterNode, UIDNode




# Create your views here.
def generate_uid(request: HttpRequest):

    request_body = json.loads(request.body)
    strict_parent_validation = request_body.get('strict_parent_validation', False)
    parent_uid = request_body.get('parent_uid', None)
    create_node = request_body.get('create_node', True)
    parent_node = UIDNode.get_node_by_uid(parent_uid)

    if parent_node is None:
        if strict_parent_validation:
            return HttpResponse("{ 'error': 'Parent node not found' }", status=404, content_type='application/json')
        else:
            parent_node = UIDNode.create_node(parent_uid,)

    

    counter_node = CounterNode.increment()

    uid = f"{counter_node.counter:08x} {counter_node.updated_at}"

    return HttpResponse("{ 'uid': '" + str(uid) + "' }", content_type='application/json')