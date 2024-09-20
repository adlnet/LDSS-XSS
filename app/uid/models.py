from django.db import models
from neomodel import StructuredNode, StringProperty, DateTimeProperty, BooleanProperty, IntegerProperty

# Create your models here.

class UIDNode(StructuredNode):
    uid = StringProperty(unique_index=True)
    created_at = DateTimeProperty(default_now=True)

class CounterNode(StructuredNode):
    counter = IntegerProperty(default=0)
    updated_at = DateTimeProperty(default_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get(cls):
        counter = cls.nodes.first()
        if counter is None:
            counter  = cls.create()
        return counter

    @classmethod
    def create(cls):
        counter = cls()
        counter.save()
        return counter
