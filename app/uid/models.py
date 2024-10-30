from django.db import models
# from django.contrib import admin
from neomodel import StringProperty, DateTimeProperty, BooleanProperty, RelationshipTo, RelationshipFrom, StructuredNode, IntegerProperty
from datetime import datetime
import time  # Import time module to use sleep
from neomodel import db  # Ensure you have access to the Neo4j database connection
from django_neomodel import DjangoNode
import logging
from django.db import transaction  # Import transaction atomic
import re

logger = logging.getLogger(__name__)

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

class GeneratedUIDLog(models.Model):
    uid = models.CharField(max_length=255, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generator_id = models.CharField(max_length=255)  # Track the generator instance

    class Meta:
        verbose_name = "Generated UID Log"
        verbose_name_plural = "Generated UID Logs"

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
                    logger.debug("Initialized new UIDCounter with default counter value: 0")
            except Exception as e:
                print(f"Error accessing Neo4j: {e}")  # Handle logging or errors appropriately
            else:
                logger.debug(f"Retrieved existing UIDCounter with counter value: {cls._cached_instance.counter}")
        return cls._cached_instance
        
    @classmethod
    def increment(cls):
        with transaction.atomic():  # Ensure atomic operation
            instance = cls.get_instance()
            logger.debug(f"Current counter before increment: {instance.counter}")
            current_value = instance.counter
            logger.debug(f"Current counter before increment: {current_value}")
            #instance.counter += 1
            instance.counter = current_value + 1
            logger.debug(f"Counter after increment: {instance.counter}")
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
        #cls.objects.get_or_create(id=1)  # Ensure a single instance
        cls.objects.get_or_create(id=1, defaults={'counter_value': 0})
        
# Initialize the UID Generator
#uid_generator = UIDGenerator()

uid_generator = None

def get_uid_generator():
    global uid_generator
    if uid_generator is None:
        if not check_neo4j_connection():  # Check connection when first needed
            raise RuntimeError("Neo4j service is not available.")
        uid_generator = UIDGenerator()
    return uid_generator

# UID Compliance check
def is_uid_compliant(uid):
    """Check if the UID complies with the specified pattern."""
    return bool(re.match(UID_PATTERN, uid))

# Refactored UID Generator that manages both Neo4j and DjangoNode and confirms Neo4j is available
class UIDGenerator:
    def __init__(self):
        #self.generator_id = generator_id  # Unique ID for this generator instance
        if not check_neo4j_connection():
            raise RuntimeError("Neo4j service is not available.")
        self.counter = UIDCounter.get_instance()
        self.counter_obj = UIDCounter.nodes.get_or_none()
        if self.counter_obj is None:
            self.counter_obj = UIDCounter.create_node()
        self.last_uid = None

# Updated with checks for collision detection, compliance detection, sequential order and regeneration.
    def generate_uid(self):
        uid_value = self.counter.increment()
        self.generator_id = uid_value.generator_id  # Unique ID for this generator instance
        attempts = 0 # Initialize attempts here change as needed
        
        while True:
            new_uid = f"0x{uid_value:08x}"
            #new_uid = f"0x{self.counter_obj.counter:08x}"
            #return f"0x{self.counter_obj.counter:08x}"
        
            # Collision check
            #if len(UIDNode.nodes.filter(uid=new_uid)) > 0:
            while len(UIDNode.nodes.filter(uid=new_uid)) > 0:
                logger.warning(f"UID collision detected for {new_uid}. Regenerating UID.")
                #suffix = 1
                attempts += 1

                # Adjust the UID by incrementing the suffix until a unique UID is found
                suffix = 1
                new_uid = f"0x{uid_value + suffix:08x}"
                while len(UIDNode.nodes.filter(uid=new_uid)) > 0:
                    #new_uid = f"0x{self.counter.counter + suffix:08x}"
                    suffix += 1  # Increment suffix for the next attempt
                    #attempts +=1 # Count attempts
                logger.info(f"Adjusted UID to {new_uid} to resolve collision.")
            
            # If too many attempts, increment base counter
            if attempts >= COLLISION_THRESHOLD:  # Define Collision threshold
                logger.info(f"Too many collisions for base UID {uid_value}. Incrementing counter.")
                self.counter.increment()  # Adjust base counter
                attempts = 0  # Reset attempts
                break  # Break out to start over with new base UID
            logger.info(f"Adjusted UID to {new_uid} to resolve collision.")
        
            # Compliance check
            if not is_uid_compliant(new_uid):
                logger.warning(f"Generated UID {new_uid} is not compliant with the expected pattern.")
                continue
            
            # Sequential order check
            if hasattr (self, 'last_uid'):
                if self.last_uid is not None and int(new_uid, 16) <= int(self.last_uid, 16):
                    logger.warning(f"UID {new_uid} is not sequential. Regenerating UID.")
                    self.counter.increment()  # Force increment
                    continue
            
            # Update the last issued UID
            self.last_uid = new_uid # Save the last generated UID
            new_uid = f"0x{uid_value:08x}"
            LastGeneratedUID.save_last_generated_uid(new_uid)

            # Log the generated UID
            GeneratedUIDLog.objects.update_or_create(uid=new_uid, defaults={'generator_id': self.generator_id})

            return new_uid
    
# Retrieve Last Generated UID
    def get_last_generated_uid():
        last_uid_record = LastGeneratedUID.objects.first()
        return last_uid_record.uid if last_uid_record else None
    
uid_singleton = UIDGenerator()

# Neo4j UID Node
class UIDNode(DjangoNode):
    uid = StringProperty(default=lambda: uid_singleton.generate_uid())
    namespace = StringProperty(required=True)
    updated_at = DateTimeProperty(default_now=True)
    created_at = DateTimeProperty(default_now=True)
    echelon_level = StringProperty(required=True)  # Add this line to define echelon levels

    children = RelationshipTo('UIDNode', 'HAS_CHILD')
    lcv_terms = RelationshipTo('LCVTerm', 'HAS_LCV_TERM')
    provider = RelationshipFrom('Provider', 'HAS_LCV_TERM')

    @classmethod
    def get_node_by_uid(cls, uid: str, namespace: str):
        return cls.nodes.get_or_none(uid=uid, namespace=namespace)
    
    @classmethod
    def create_node(cls, uid, namespace, echelon_level) -> 'UIDNode':
        # Find existing Node
        existing_node = cls.get_node_by_uid(uid=None, namespace=namespace)  # Adjust the filter as needed
        if existing_node:
            logger.info(f"Node already exists for namespace: {namespace}. Reusing existing UID: {existing_node.uid}.")
            return existing_node  # Return the existing node if found
        
        uid_node = cls(uid=uid, namespace=namespace, echelon_level=echelon_level)
        uid_node.save()
        return uid_node
    
    class Meta:
        app_label = 'uid'

# Neo4j Counter Node
#class CounterNode(DjangoNode):
 #   counter = IntegerProperty(default=0)
  #  updated_at = DateTimeProperty(default=lambda: datetime.now())

   # @classmethod
    #def get(cls):
     #   counter_node = cls.nodes.first_or_none()
      #  if counter_node is None:
       #     return cls.create_node()
        #return counter_node

  #  @classmethod
   # def create_node(cls):
    #    counter = cls()
     #   counter.save()
      #  return counter
    
    #@classmethod
    #def increment(cls):
     #   counter = cls.get()
      #  counter.counter += 1
       # counter.updated_at = datetime.now()
        #counter.save()
        #return counter
    
    #class Meta: 
      #  app_label = 'uid'

# Provider and LCVTerms now Nodes
class Provider(DjangoNode):
    uid = StringProperty(default=lambda: uid_singleton.generate_uid(), unique_index=True)
    name = StringProperty(required=True)
    echelon_level = StringProperty(required=True)  # Required for echelon check
    lcv_terms = RelationshipTo('LCVTerm', 'HAS_LCV_TERM')

    class Meta:
        app_label = 'uid'

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


class LCVTerm(DjangoNode):
    uid = StringProperty(default=lambda: uid_singleton.generate_uid(), unique_index=True)
    term = StringProperty(required=True)
    ld_lcv_structure = StringProperty()
    echelon_level = StringProperty(required=True)  # Required for echelon check
    provider = RelationshipFrom('Provider', 'HAS_LCV_TERM')

    class Meta:
        app_label = 'uid'

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
    uid = StringProperty(default=lambda: uid_singleton.generate_uid(), unique_index=True)
    name = StringProperty(required=True)
    terms = RelationshipTo(LCVTerm, 'HAS_TERM')

    def add_term(self, term):
        self.terms.connect(term)

    def get_terms(self):
        return self.terms.all()

# Adding reporting by echelon level
def report_uids_by_echelon(echelon_level):
    """Retrieve UIDs issued at a specific echelon level."""
    nodes = UIDNode.nodes.filter(echelon_level=echelon_level)
    return [node.uid for node in nodes]

def get_uid_generator(generator_id: str):
    return UIDGenerator(generator_id=generator_id)

def report_all_uids():
    """Retrieve all UIDs issued in the enterprise."""
    nodes = UIDNode.nodes.all()
    return [node.uid for node in nodes]

# Adding Last Generated UID
class LastGeneratedUID(models.Model):
    uid = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Last Generated UID"
        verbose_name_plural = "Last Generated UIDs"

    @classmethod
    def save_last_generated_uid(cls, new_uid):
        """Save the last generated UID to the database."""
        with transaction.atomic():  # Ensure atomic operation
        #LastGeneratedUID.objects.update_or_create(defaults={'uid': new_uid}, id=1)
            cls.objects.update_or_create(defaults={'uid': new_uid}, id=1)

    @classmethod
    def get_last_generated_uid():
        """Retrieve the last generated UID from the database."""
        last_uid_record = LastGeneratedUID.objects.first()
        return last_uid_record.uid if last_uid_record else None
    
class LastGeneratedUID(StructuredNode):
    uid = StringProperty(default=None)

    @classmethod
    def get_last_generated_uid(cls):
        """Retrieve the last generated UID from Neo4j."""
        last_uid_record = cls.nodes.first_or_none()
        return last_uid_record.uid if last_uid_record else None

    @classmethod
    def save_last_generated_uid(cls, new_uid):
        """Save the last generated UID to Neo4j."""
        last_uid_record = cls.nodes.first_or_none()
        if last_uid_record:
            last_uid_record.uid = new_uid
            last_uid_record.save()
        else:
            cls(uid=new_uid).save()



# Reporting fucntion for all generated UIDs
def report_all_generated_uids():
    """Retrieve all generated UIDs from the log."""
    logs = GeneratedUIDLog.objects.all()
    return [(log.uid, log.generated_at, log.generator_id) for log in logs]