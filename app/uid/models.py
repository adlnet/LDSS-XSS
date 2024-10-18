from django.db import models
from neomodel import StructuredNode, StringProperty, DateTimeProperty, BooleanProperty, IntegerProperty, RelationshipTo
from datetime import datetime
# from .utils import generate_uid # Import from generate_uid
# import uuid
# import hashlib

# Create your models here.

class UIDGenerator:
    def __init__(self):
        self.counter = 0

    def generate_uid(self):
        self.counter += 1
        return f"UID{self.counter:06d}"  # Zero-padded to 6 digits

# Intilialize the UID Generator
uid_generator = UIDGenerator()
#def generate_uid(input_string):
#    return hashlib.sha256(input_string.encode()).hexdigest()[:36] #Using a Hashlib we are generating our own UID.

class UIDNode(StructuredNode):
    uid = StringProperty(default=lambda:uid_generator.generate_uid()) # Updated to use UID Generator counter
    # uid = StringProperty(default=lambda:generate_uid(str(datetime.now()))) # Updated string to no no longer use uuid4
    # uid = StringProperty(default=lambda:str(uuid.uuid4())) # UUID if UID is not provided to ensure uniqueness and avoids conflits
    # Should this have a TermID or Term value and Definition value? 
    # Is the UID Service just supposed to generate UID's or is it supposed to store the relationships between different terms. 
    namespace = StringProperty(required=True)
    updated_at = DateTimeProperty(default_now=True) # Better time stamp handeling.
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
    updated_at = DateTimeProperty(default=lambda: datetime.now())

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


class Provider(models.Model):
    uid = models.CharField(default=lambda: uid_generator.generate_uid(), max_length=36, editable=False, unique=True)
    #uid = models.CharField(default=lambda: generate_uid(str(datetime.now())), max_length=36, editable=False, unique=True)
    #uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)

class LCVTerm(models.Model):
    uid = models.CharField(default=lambda: uid_generator.generate_uid(), max_length=36, editable=False, unique=True)
    #uid = models.CharField(default=lambda: generate_uid(str(datetime.now())), max_length=36, editable=False, unique=True)
    #uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    term = models.CharField(max_length=255)
    ld_lcv_structure = models.CharField(max_length=255)  # Adjust as needed

class LanguageSet(models.Model):  # Assuming this is the model for xBOM
    uid = models.CharField(default=lambda: uid_generator.generate_uid(), max_length=36, editable=False, unique=True)
    name = models.CharField(max_length=255)
    terms = models.ManyToManyField(LCVTerm, related_name='language_sets')