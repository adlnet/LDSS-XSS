from django.db import models
from neomodel import StructuredNode, StringProperty, DateTimeProperty, BooleanProperty, IntegerProperty
from datetime import datetime
# Create your models here.

class UIDNode(StructuredNode):
    uid = StringProperty()
    term = StringProperty(required=True)
    namespace = StringProperty(required=True)
    updated_at = DateTimeProperty()
    created_at = DateTimeProperty(default_now=True)

    @classmethod
    def get_node_by_uid(cls, uid: str, namespace: str) -> 'UIDNode' | None:
        return cls.nodes.get_or_none(uid=uid, namespace=namespace)
    @classmethod
    def create_node(cls, uid, term, namespace) -> 'UIDNode':
        uid_node = cls(uid=uid, term=term, namespace=namespace)
        uid_node.save()
        return uid_node
    
class CounterNode(StructuredNode):
    counter = IntegerProperty(default=0)
    updated_at = DateTimeProperty(default_now=True)

    @classmethod
    def get(cls) -> 'CounterNode':
        counter_node = cls.nodes.first_or_none()
        if counter_node is None:
            return cls.create_node()
        return counter_node

    @classmethod
    def create_node(cls) -> 'CounterNode':
        counter = cls()
        counter.save()
        return counter
    
    @classmethod
    def increment(cls) -> 'CounterNode':
        counter = cls.get()
        counter.counter += 1
        counter.updated_at = datetime.now()
        counter.save()
        return counter
