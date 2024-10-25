from django.db import models
# from django.contrib import admin
from neomodel import StringProperty, DateTimeProperty, BooleanProperty, RelationshipTo, RelationshipFrom, StructuredNode, IntegerProperty
from datetime import datetime
import time  # Import time module to use sleep
from neomodel import db  # Ensure you have access to the Neo4j database connection

# Function to check Neo4j connection
def check_neo4j_connection():
    for attempt in range(5):  # Retry a few times
        try:
            db.cypher_query("RETURN 1")  # Simple query to test connection
            return True
        except Exception:
            time.sleep(1)  # Wait before retrying
    return False

# Creating the UIDCounter as Neo4j Node
class UIDCounter(StructuredNode):
    counter = IntegerProperty(default=0)
    
    _cached_instance = None #added for caching

    @classmethod
    def get_instance(cls):
        if cls._cached_instance is None:
            try:
                cls._cached_instance = cls.nodes.first_or_none()
                if not cls._cached_instance:
                    cls._cached_instance = cls()
                    cls._cached_instance.save()
            except Exception as e:
                print(f"Error accessing Neo4j: {e}")  # Handle logging or errors appropriately
        return cls._cached_instance
        
        #instance = cls.nodes.first_or_none()
        #if not instance:
         #   instance = cls()
         #   instance.save()
       # return instance

    @classmethod
    def increment(cls):
        instance = cls.get_instance()
        instance.counter += 1
        instance.save()
        return instance.counter

# Django model for admin management
class UIDCounterDjangoModel(models.Model):
    counter_value = models.IntegerField(default=0)

    class Meta:
        verbose_name = "UID Counter"
        verbose_name_plural = "UID Counters"

    @classmethod
    def initialize(cls):
        """Ensure a counter exists in the Django model."""
        cls.objects.get_or_create(id=1)  # Ensure a single instance
        
# Initialize UIDGenerator after confirming Neo4j is available
if not check_neo4j_connection():
    raise RuntimeError("Neo4j service is not available.")

# Refactored UID Generator that manages both Neo4j and DjangoNode
class UIDGenerator:
    def __init__(self):
        self.counter = UIDCounter.get_instance()
        self.counter_obj = UIDCounter.nodes.get_or_none()
        if self.counter_obj is None:
            self.counter_obj = UIDCounter.create_node()

    def generate_uid(self):
        uid_value = self.counter.increment()
        return f"0x{self.counter_obj.counter:08x}"

# Initialize the UID Generator
uid_generator = UIDGenerator()

# Neo4j UID Node
class UIDNode(StructuredNode):
    uid = StringProperty(default=lambda: uid_generator.generate_uid())
    namespace = StringProperty(required=True)
    updated_at = DateTimeProperty(default_now=True)
    created_at = DateTimeProperty(default_now=True)

    children = RelationshipTo('UIDNode', 'HAS_CHILD')
    lcv_terms = RelationshipTo('LCVTerm', 'HAS_LCV_TERM')
    provider = RelationshipFrom('Provider', 'HAS_LCV_TERM')

    @classmethod
    def get_node_by_uid(cls, uid: str, namespace: str):
        return cls.nodes.get_or_none(uid=uid, namespace=namespace)
    
    @classmethod
    def create_node(cls, uid, namespace) -> 'UIDNode':
        uid_node = cls(uid=uid, namespace=namespace)
        uid_node.save()
        return uid_node

# Neo4j Counter Node
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

# Django Provider Model for Admin
class ProviderDjangoModel(models.Model):
    uid = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        # Create or update the Neo4j Provider node
        provider = Provider(uid=self.uid, name=self.name)
        provider.save()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Provider"
        verbose_name_plural = "Providers"

class LCVTerm(StructuredNode):
    uid = StringProperty(default=lambda: uid_generator.generate_uid(), unique_index=True)
    term = StringProperty(required=True)
    ld_lcv_structure = StringProperty()
    provider = RelationshipFrom('Provider', 'HAS_LCV_TERM')

# Django LCVTerm Model for Admin
class LCVTermDjangoModel(models.Model):
    uid = models.CharField(max_length=255, unique=True)
    term = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        # Create or update the Neo4j LCVTerm node
        lcv_term = LCVTerm(uid=self.uid, term=self.term)
        lcv_term.save()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "LCV Term"
        verbose_name_plural = "LCV Terms"

# LanguageSet now a Node
class LanguageSet(StructuredNode):
    uid = StringProperty(default=lambda: uid_generator.generate_uid(), unique_index=True)
    name = StringProperty(required=True)
    terms = RelationshipTo(LCVTerm, 'HAS_TERM')

    def add_term(self, term):
        self.terms.connect(term)

    def get_terms(self):
        return self.terms.all()

