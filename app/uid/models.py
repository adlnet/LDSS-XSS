from django.db import models
from neomodel import StructuredNode, StringProperty, DateTimeProperty, BooleanProperty, IntegerProperty
from datetime import datetime
# Create your models here.

class UIDNode(StructuredNode):
    uid = StringProperty(unique_index=True)
    created_at = DateTimeProperty(default_now=True)

class CounterNode(StructuredNode):
    counter = IntegerProperty(default=0)
    updated_at = DateTimeProperty(default_now=True)

    @classmethod
    def get(cls):
        counter_node = cls.nodes.first_or_none()
        if counter_node is None:
            return cls.create_node()
        return counter_node

    @classmethod
    def create_node(cls):
        counter = cls()
        counter.save()
        return counter
    
    @classmethod
    def increment(cls):
        counter = cls.get()
        counter.counter += 1
        counter.updated_at = datetime.now()
        counter.save()
        return counter
