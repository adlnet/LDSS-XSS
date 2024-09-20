from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from uuid import uuid5, NAMESPACE_URL
import json
from neomodel import db
from .models import CounterNode




# Create your views here.
def generate_uid(request: HttpRequest):

    counter_node = CounterNode.get()

    
    
    #uid = f"{count:08x}"
    

    return HttpResponse("{ 'uid': '" + str(counter_node) + " }", content_type='application/json')