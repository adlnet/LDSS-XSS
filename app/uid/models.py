from django.db import models, transaction #Import Models and transaction atomic
from neomodel import db, StringProperty, DateTimeProperty, BooleanProperty, RelationshipTo, RelationshipFrom, StructuredNode, IntegerProperty, NodeSet
from datetime import datetime
import time, logging, re # Import time module to use sleep, Logging and re
from django_neomodel import DjangoNode
from collections import defaultdict
from typing import List

logger = logging.getLogger(__name__)

GLOBAL_PROVIDER_OWNER_UID = "0xFFFFFFFF"
UID_PATTERN = r"^0x[0-9A-Fa-f]{8}$"
COLLISION_THRESHOLD = 5  # Number of attempts before adjusting the base counter

# Function to check Neo4j connection
def check_neo4j_connection():
    for attempt in range(5):  # Retry a few times
        try:
            db.cypher_query("RETURN 1")  # Simple query to test connection
            return True
        except Exception:
            time.sleep(1)  # Wait before retrying
    return False

# Generated Logs to track instance, time of generation, uid, provider and lcv terms
class GeneratedUIDLog(models.Model):
    uid = models.CharField(max_length=255, default="UNKNOWN")
    uid_full = models.CharField(max_length=255, default="UNKNOWN")
    generated_at = models.DateTimeField(auto_now_add=True)
    generator_id = models.CharField(max_length=255)
    provider = models.CharField(max_length=255, null=True)
    lcv_terms = models.CharField(max_length=255, null=True)

    class Meta:
        verbose_name = "Generated UID Log"
        verbose_name_plural = "Generated UID Logs"

class UIDCounter(StructuredNode):
    owner_uid = StringProperty(required=True)
    counter = IntegerProperty(default=0)
    
    # _cached_instance = None #added for caching
    _cache = {}

    @classmethod
    def _get_instance(cls, owner_uid: str) -> 'UIDCounter':
        if owner_uid in cls._cache:
            return cls._cache[owner_uid]
    
        # try:
        # instances = cls.get_or_create(owner_uid=owner_uid)
        nodes = UIDCounter.nodes
        assert isinstance(nodes, NodeSet)
        result = nodes.get_or_none(owner_uid=owner_uid)

        if result is None:
            instance = UIDCounter(owner_uid=owner_uid)
            instance.save()
            cls._cache[owner_uid] = instance
            return instance
        
        if isinstance(result, list):
            instance = result[0]
        else:
            instance = result
        
        assert isinstance(instance, UIDCounter)
        cls._cache[owner_uid] = instance
        return instance

    @classmethod
    def increment(cls, owner_uid: str):
        with transaction.atomic():  # Ensure atomic operation
            instance = cls._get_instance(owner_uid)
            current_value = instance.counter
            instance.counter = current_value + 1
            instance.save()
            return instance.counter

# # Django model for admin management
# class UIDCounterDjangoModel(models.Model):
#     counter_value = models.IntegerField(default=0)

#     class Meta:
#         verbose_name = "UID Counter"
#         verbose_name_plural = "UID Counters"

#     @classmethod
#     def initialize(cls):
#         """Ensure a counter exists in the Django model."""
#         #cls.objects.get_or_create(id=1)  # Ensure a single instance
#         cls.objects.get_or_create(id=1, defaults={'counter_value': 0})
        
# # Initialize the UID Generator
# uid_generator = None

# def get_uid_generator():
#     global uid_generator
#     if uid_generator is None:
#         if not check_neo4j_connection():  # Check connection when first needed
#             raise RuntimeError("Neo4j service is not available.")
#         uid_generator = UIDGenerator()
#     return uid_generator

# UID Compliance check
def is_uid_compliant(uid):
    """Check if the UID complies with the specified pattern."""
    return bool(re.match(UID_PATTERN, uid))

def report_malformed_uids():
    """Generate a report of all malformed UIDs."""
    malformed_uids = []
    logs = GeneratedUIDLog.objects.all()
    
    for log in logs:
        if not is_uid_compliant(log.uid):
            malformed_uids.append(log.uid)
    
    return malformed_uids


# Neo4j UID Node
class UIDNode(DjangoNode):
    uid = StringProperty(required=True)
    # namespace = StringProperty(required=True)
    updated_at = DateTimeProperty(default_now=True)
    created_at = DateTimeProperty(default_now=True)

    # children = RelationshipTo('UIDNode', 'HAS_CHILD')
    # lcv_terms = RelationshipTo('LCVTerm', 'HAS_LCV_TERM')
    # provider = RelationshipTo('Provider', 'HAS_PROVIDER')

    @classmethod
    def get_node_by_uid(cls, uid: str):
        # return cls.nodes.get_or_none(uid=uid, namespace=namespace)
        return cls.nodes.get_or_none(uid=uid)
    
    @classmethod
    def create_node(cls, owner_uid: str) -> 'UIDNode':
        # # Find existing Node
        # existing_node = cls.get_node_by_uid(uid=None, namespace=namespace)  # Adjust the filter as needed
        # if existing_node:
        #     logger.info(f"Node already exists for namespace: {namespace}. Reusing existing UID: {existing_node.uid}.")
        #     return existing_node  # Return the existing node if found
        
        # uid_node = cls(uid=uid, namespace=namespace)
        uid_value = generate_uid(owner_uid)
        uid_node = cls(uid=uid_value)
        uid_node.save()
        return uid_node
    
    class Meta:
        app_label = 'uid'


# Refactored UID Generator that manages both Neo4j and DjangoNode and confirms Neo4j is available
def generate_uid(owner_uid) -> str:

    uid_value = UIDCounter.increment(owner_uid=owner_uid)
    attempts = 0 # Initialize attempts here change as needed
    
    while True:
        new_uid = f"0x{uid_value:08x}"
        
        # # Collision check
        # while len(UIDNode.nodes.filter(uid=new_uid, owner_uid=owner_uid)) > 0:
        #     logger.warning(f"UID collision detected for {new_uid}. Regenerating UID.")
        #     attempts += 1

        #     # Adjust the UID by incrementing the base value directly to resolve the collision until a unique UID is found
        #     uid_value += 1
        #     new_uid = f"0x{uid_value:08x}"
        #     logger.info(f"Adjusted UID to {new_uid} to resolve collision.")
        
        # Collision threshold, if too many attempts, break, reset attempts and increment base counter
        if attempts >= COLLISION_THRESHOLD:
            logger.error(f"Too many collisions for base UID {uid_value}. Incrementing counter.")
            # counter.increment()
            attempts = 0
            break
        
        logger.info(f"Adjusted UID to {new_uid} to resolve collision.")
    
        # Compliance check
        if not is_uid_compliant(new_uid):
            logger.error(f"Generated UID {new_uid} is not compliant with the expected pattern.")
            continue
        
        # # Sequential order check, if not sequential force increment and regenerate UID
        # if hasattr (self, 'last_uid'):
        #     if self.last_uid is not None and int(new_uid, 16) <= int(self.last_uid, 16):
        #         logger.warning(f"UID {new_uid} is not sequential. Regenerating UID.")
        #         self.counter.increment()
        #         continue
        
        # Update and save the last issued UID
        #
        # uid = models.CharField(max_length=255, unique=True)
        # uid_full = models.CharField(max_length=255, unique=True)
        # generated_at = models.DateTimeField(auto_now_add=True)
        # generator_id = models.CharField(max_length=255)
        # provider = models.CharField(max_length=255, null=True)
        # lcv_terms = models.CharField(max_length=255, null=True)
        uid_full = f"{owner_uid}-{new_uid}"
        GeneratedUIDLog.objects.create(uid=new_uid, uid_full=uid_full)

        # # Log the generated UID
        # GeneratedUIDLog.objects.update_or_create(uid=new_uid, defaults={'generator_id': self.generator_id})

        return new_uid
    
    # # Retrieve Last Generated UID
    # def get_last_generated_uid():
    #     last_uid_record = LastGeneratedUID.objects.first()
    #     return last_uid_record.uid if last_uid_record else None
    
# uid_singleton = UIDGenerator()

# Provider and LCVTerms now Nodes
class Provider(DjangoNode):
    # uid = StringProperty(unique_index=True)
    name = StringProperty(required=True)
    default_uid = StringProperty(required=True)

    uid = RelationshipTo('UIDNode', 'HAS_UID')
    uid_counter = RelationshipTo('UIDCounter', 'HAS_UID_COUNTER')
    # lcv_terms = RelationshipTo('LCVTerm', 'HAS_LCV_TERM')

    class Meta:
        app_label = 'uid'

    @classmethod
    def create_provider(cls, name) -> 'Provider':
        
        uid_node = UIDNode.create_node(owner_uid=GLOBAL_PROVIDER_OWNER_UID)
        counter_node = UIDCounter._get_instance(owner_uid=uid_node.uid)

        provider = Provider(name=name, default_uid=uid_node.uid)
        provider.save()
        provider.uid.connect(uid_node)
        provider.uid_counter.connect(counter_node)
        provider.save()

        return provider
    
    @classmethod
    def get_provider_by_name(cls, name):
        provider_nodes = Provider.nodes
        assert isinstance(provider_nodes, NodeSet)
        result = provider_nodes.get_or_none(name=name)

        if result is None:
            raise Exception(f"CANNOT FIND REQUESTED PROVIDER: {name}")

        provider = result
        if isinstance(provider, list):
            provider = result[0]

        assert isinstance(provider, Provider)
        return provider
    
    def get_current_uid(self):
        current_uid = self.default_uid

        current_uid_node = self.uid.end_node()
        if current_uid_node is not None:
            assert isinstance(current_uid_node, UIDNode)
            current_uid = current_uid_node.uid

        return current_uid

# Django Provider Model for Admin
class ProviderDjangoModel(models.Model):
    # uid = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    # default_uid = StringProperty(required=True)

    def save(self, *args, **kwargs):
        # Create or update the Neo4j Provider node
        provider = Provider.create_provider(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Provider"
        verbose_name_plural = "Providers"

# LCV Terms model for DjangoNode
class LCVTerm(DjangoNode):
    default_uid = StringProperty(required=True)
    default_uid_chain = StringProperty(default="")

    term = StringProperty(required=True)
    ld_lcv_structure = StringProperty()
    echelon_level = StringProperty(required=True)  # Required for echelon check

    uid = RelationshipTo('UIDNode', 'HAS_UID')
    provider = RelationshipFrom('Provider', 'HAS_LCV_TERM')

    class Meta:
        app_label = 'uid'

    @classmethod
    def create_term(cls, provider_name: str, term: str, structure: str, echelon_level: str):
        
        provider = Provider.get_provider_by_name(provider_name)
        assert isinstance(provider, Provider)
                
        uid_node = UIDNode.create_node(
            owner_uid=provider.default_uid
        )

        lcv_term = LCVTerm(term=term, echelon_level=echelon_level, ld_lcv_structure=structure)
        lcv_term.default_uid = uid_node.uid
        lcv_term.default_uid_chain = f"{provider.default_uid}-{uid_node.uid}" 
        lcv_term.save()
        lcv_term.uid.connect(uid_node)
        lcv_term.provider.connect(provider)
        lcv_term.save()
        
        return lcv_term
    
    def get_current_local_uid_chain(self):

        current_uid = self.default_uid
        current_uid_node = self.uid.end_node()
        if self.uid.end_node() is not None:
            current_uid = current_uid_node.uid
        
        current_provider_uid = ""
        current_provider_node = self.provider.start_node()
        if current_provider_node is None:
            assert isinstance(current_provider_node, Provider)
            current_provider_uid = current_provider_node.get_current_uid()
        
        return f"{current_provider_uid}-{current_uid}"

# Django LCVTerm Model for Admin
class LCVTermDjangoModel(models.Model):
    # uid = models.CharField(max_length=255, unique=True)
    provider_name = models.CharField(max_length=255)
    term = models.CharField(max_length=255)
    echelon = models.CharField(max_length=255)
    structure = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        # Create or update the Neo4j LCVTerm node
        lcv_term = LCVTerm.create_term(provider_name=self.provider_name, term=self.term, echelon_level=self.echelon, structure=self.structure)
        lcv_term.save()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "LCV Term"
        verbose_name_plural = "LCV Terms"

# # LanguageSet now a Node
# class LanguageSet(StructuredNode):
#     uid = StringProperty(default=lambda: uid_singleton.generate_uid(), unique_index=True)
#     name = StringProperty(required=True)
#     terms = RelationshipTo(LCVTerm, 'HAS_TERM')

#     def add_term(self, term):
#         self.terms.connect(term)

#     def get_terms(self):
#         return self.terms.all()

# Adding reporting by echelon level
def report_uids_by_echelon(echelon_level):
    """Retrieve UIDs issued at a specific echelon level."""
    nodes = UIDNode.nodes
    assert isinstance(nodes, NodeSet)
    nodes = nodes.filter(echelon_level=echelon_level)
    return [node.uid for node in nodes]

def report_all_uids():
    """Retrieve all UIDs issued in the enterprise."""
    nodes = UIDNode.nodes.all()
    return [node.uid for node in nodes]

# Reporting function for all generated UIDs
def report_all_generated_uids():
    """Retrieve all generated UIDs from the log."""
    logs = GeneratedUIDLog.objects.all()
    return [(log.uid, log.uid_full, log.generated_at, log.generator_id) for log in logs]

def report_all_term_uids():
    """
    Query and return all UID chains from every known Term.
    """
    term_nodes = LCVTerm.nodes.all()
    return [term.get_current_local_uid_chain() for term in term_nodes]

# # Reporting all UID collision
# def report_uid_collisions():
#     """Generate a report of potential UID collisions across all UID microservices."""
#     # Retrieve all UID logs
#     logs = GeneratedUIDLog.objects.all()

#     # Dictionary to track UIDs by (parent_id, uid)
#     uid_dict = defaultdict(list)

#     for log in logs:
#         # Store the combination of parent_id and uid
#         uid_dict[(log.parent_id, log.uid)].append(log)

#         # Collect UIDs for Providers
#         providers = ProviderDjangoModel.objects.all()
#         for provider in providers:
#             uid_dict[(provider.uid, provider.uid)].append(provider)

#         # Collect UIDs for LCVTerms
#         lcv_terms = LCVTermDjangoModel.objects.all()
#         for lcv_term in lcv_terms:
#             uid_dict[(lcv_term.uid, lcv_term.uid)].append(lcv_term)

#     # Find collisions (where length > 1)
#     collisions = {key: value for key, value in uid_dict.items() if len(value) > 1}
#     return collisions