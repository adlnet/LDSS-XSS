from django.db import models
from neomodel import StructuredNode, StringProperty, DateTimeProperty, BooleanProperty, IntegerProperty, RelationshipTo
from datetime import datetime
# Create your models here.

class UIDNode(StructuredNode):
    uid = StringProperty()
    # Should this have a TermID or Term value and Definition value? 
    # Is the UID Service just supposed to generate UID's or is it supposed to store the relationships between different terms. 
    namespace = StringProperty(required=True)
    updated_at = DateTimeProperty()
    created_at = DateTimeProperty(default_now=True)

    children = RelationshipTo('UIDNode', 'HAS_CHILD')

    @classmethod
    def get_node_by_uid(cls, uid: str, namespace: str):
        return cls.nodes.get_or_none(uid=uid, namespace=namespace)
    @classmethod
    def create_node(cls, uid,  namespace) -> 'UIDNode':
        uid_node = cls(uid=uid,  namespace=namespace)
        uid_node.save()
        return uid_node
    
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
