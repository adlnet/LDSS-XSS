from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from uuid import uuid5, NAMESPACE_URL
import json
from neomodel import db
from .models import CounterNode




# Create your views here.
def generate_uid(request: HttpRequest):

    counter_node = CounterNode.increment()

    uid = f"{counter_node.counter:08x} {counter_node.updated_at}"

    return HttpResponse("{ 'uid': '" + str(uid) + "' }", content_type='application/json')