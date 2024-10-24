from django.db import models
from django.contrib import admin
from neomodel import StringProperty, DateTimeProperty, BooleanProperty, RelationshipTo, RelationshipFrom
from neomodel import StructuredNode, IntegerProperty
from datetime import datetime
# from .utils import generate_uid # Import from generate_uid
# import uuid
# import hashlib

# Updated Models now will utilize the Neo4j UIDCounter directly without depending on the Django ORM, while keeping the UIDCounterDjangoModel for admin management.

#Creating the UIDcounter as Neo4j Node
class UIDCounter(StructuredNode):
    counter = IntegerProperty(default=0)


    @classmethod
    def get_instance(cls):
        instance = cls.nodes.first_or_none()
        if not instance:
            instance = cls()
            instance.save()
        return instance  # Method create a new Counter node if none exists

    @classmethod
    def increment(cls):
        instance = cls.get_instance()
        instance.counter += 1
        instance.save()
        return instance.counter # Method increments the counter and save its last place.

# Create a Django model to facilitate admin management
class UIDCounterDjangoModel(models.Model):
    counter_value = models.IntegerField(default=0)

    class Meta:
        verbose_name = "UID Counter"
        verbose_name_plural = "UID Counters"

    @classmethod
    def initialize(cls):
        """Ensure a counter exists in the Django model."""
        cls.objects.get_or_create(id=1)  # Ensure a single instance

# Refactored UID Generator that manages both Neo4j and DjangoNode
class UIDGenerator:
    def __init__(self):
        self.counter = UIDCounter.get_instance()
        #UIDCounter.initialize()  # Ensure the counter is initialized
        #UIDCounterDjangoModel.initialize()  # Ensure the Django model counter is initialized
        #self.counter_obj = UIDCounter.objects.get(id=1)
        self.counter_obj = UIDCounter.nodes.get_or_none()  # Get the counter node

        if self.counter_obj is None:
            self.counter_obj = UIDCounter.create_node()  # Create if none exists

    def generate_uid(self):
        #self.counter += 1
        uid_value = self.counter.increment()
        #self.counter_obj.counter += 1
        #self.counter_obj.save()
        #return f"UID{self.counter:06d}"  # Zero-padded to 6 digits
        return f"0x{self.counter_obj.counter:08x}"  # Now using hexadecimal for UID

# Intilialize the UID Generator
uid_generator = UIDGenerator()

#def generate_uid(input_string):
#    return hashlib.sha256(input_string.encode()).hexdigest()[:36] #Using a Hashlib we are generating our own UID.

#Neo4j UID Node
class UIDNode(StructuredNode):
    uid = StringProperty(default=lambda:uid_generator.generate_uid()) # Updated to use UID Generator counter
    # uid = StringProperty(default=lambda:generate_uid(str(datetime.now()))) # Updated string to no longer use uuid4
    # uid = StringProperty(default=lambda:str(uuid.uuid4())) # UUID if UID is not provided to ensure uniqueness and avoids conflits.
    namespace = StringProperty(required=True)
    updated_at = DateTimeProperty(default_now=True) # Better time stamp handeling.
    created_at = DateTimeProperty(default_now=True)

    children = RelationshipTo('UIDNode', 'HAS_CHILD')
    lcv_terms = RelationshipTo('LCVTerm', 'HAS_LCV_TERM')
    provider = RelationshipFrom('Provider', 'HAS_LCV_TERM')

    @classmethod
    def get_node_by_uid(cls, uid: str, namespace: str):
        return cls.nodes.get_or_none(uid=uid, namespace=namespace)
    
    @classmethod
    def create_node(cls, uid,  namespace) -> 'UIDNode':
        uid_node = cls(uid=uid,  namespace=namespace)
        uid_node.save()
        return uid_node
    
# Possible idea for Parent/child or Provider/LCVterm upstream/downstream 
    #def get_providers(self):
        #return self.providers.all()

    #def get_lcvterms(self):
        #return self.lcvterms.all()

    #def get_upstream(self)
        #providers = []
        #current_node = self
        #while current_node:
            #provider_nodes = currrent_node.get_providers()
            #if provider_nodes:
            #   provider_node = parent_nodes[0]
            # providers.append(provider_node)
            # current_node = provider_node
            # else:
            #       current_node = None
        #return providers
    
    #def get_downstream(self):
        #lcv_terms = []
        #nodes_to_visit = [self]
        #while nodes_to_visit:
            #current_node = nodes_to_visit.pop()
            #lcv_terms_nodes = current_node.get_lcv_terms()
            #lcv_terms.extend(lcv_terms_nodes)
            #nodes_to_visit.extend(lcv_terms_nodes)
        #return lcv_terms   

#NEO4J counter node
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

# Provider and LCVTerms now Nodes
class Provider(StructuredNode):
    uid = StringProperty(default=lambda: uid_generator.generate_uid(), unique_index=True)
    name = StringProperty(required=True)
    lcv_terms = RelationshipTo('LCVTerm', 'HAS_LCV_TERM')

class LCVTerm(StructuredNode):
    uid = StringProperty(default=lambda: uid_generator.generate_uid(), unique_index=True)
    term = StringProperty(required=True)
    ld_lcv_structure = StringProperty()  # Adjust as needed
    provider = RelationshipFrom('Provider', 'HAS_LCV_TERM')

# LanguageSet now a Node
class LanguageSet(StructuredNode):
    uid = StringProperty(default=lambda: uid_generator.generate_uid(), unique_index=True)
    name = StringProperty(required=True)
    terms = RelationshipTo(LCVTerm, 'HAS_TERM')

    def add_term(self, term):
        """Add a LCVTerm to this LanguageSet."""
        self.terms.connect(term)

    def get_terms(self):
        """Retrieve all LCVTerms in this LanguageSet."""
        return self.terms.all()
    
# Register UIDCounterDjangoModel in the admin
@admin.register(UIDCounterDjangoModel)
class UIDCounterAdmin(admin.ModelAdmin):
    list_display = ('id', 'counter_value')
    search_fields = ('id',)
