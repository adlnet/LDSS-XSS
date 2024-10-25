from django.db import models
from django.contrib import admin
from neomodel import StringProperty, DateTimeProperty, BooleanProperty, RelationshipTo, RelationshipFrom, StructuredNode, IntegerProperty
from datetime import datetime

# Creating the UIDCounter as Neo4j Node
class UIDCounter(StructuredNode):
    counter = IntegerProperty(default=0)

    @classmethod
    def get_instance(cls):
        instance = cls.nodes.first_or_none()
        if not instance:
            instance = cls()
            instance.save()
        return instance

    @classmethod
    def increment(cls):
        instance = cls.get_instance()
        instance.counter += 1
        instance.save()
        return instance.counter

# Create a Django model to facilitate admin management
class UIDCounterDjangoModel(models.Model):
    counter_value = models.IntegerField(default=0)

    class Meta:
        verbose_name = "UID Counter"
        verbose_name_plural = "UID Counters"

    @classmethod
    def initialize(cls):
        cls.objects.get_or_create(id=1)

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

# Register UIDCounterDjangoModel in the admin
@admin.register(UIDCounterDjangoModel)
class UIDCounterAdmin(admin.ModelAdmin):
    list_display = ('id', 'counter_value')
    search_fields = ('id',)

@admin.register(ProviderDjangoModel)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('uid', 'name')
    search_fields = ('name',)

@admin.register(LCVTermDjangoModel)
class LCVTermAdmin(admin.ModelAdmin):
    list_display = ('uid', 'term')
    search_fields = ('term',)
