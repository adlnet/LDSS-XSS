from .models import NeoAlias, NeoDefinition, NeoContext, NeoContextDescription, NeoTerm
from deconfliction_service.views import run_deconfliction
import logging
from uuid import uuid4
logger = logging.getLogger('dict_config_logger')

def run_node_creation(definition: str, context: str, context_description: str, alias: str=None):
    try:
        logger.info('Running Deconfliction')
        definition_vector_embedding, deconfliction_status, most_similar_text, highest_score = run_deconfliction(alias, definition, context, context_description)

        if deconfliction_status == 'unique':
            run_unique_definition_creation(definition=definition, context=context, context_description=context_description, definition_embedding=definition_vector_embedding, alias=alias)
        elif deconfliction_status == 'duplicate':
            run_duplicate_definition_creation(alias, most_similar_text, context, context_description)
        elif deconfliction_status == 'collision':
            run_collision_definition_creation(alias, most_similar_text, definition, context, context_description, definition_vector_embedding, highest_score)
            

    except Exception as e: 
        logger.error(f"Error in run_node_creation: {e}")
        raise e


def run_unique_definition_creation(definition, context, context_description, definition_embedding, alias):
    try:
        uid = uuid4()

        term_node, _ = NeoTerm.get_or_create(uid=uid)

        alias_node = None
        if alias:
            alias_node, _ = NeoAlias.get_or_create(alias=alias)

        definition_node, _ = NeoDefinition.get_or_create(definition=definition, definition_embedding=definition_embedding)

        context_node, _ = NeoContext.get_or_create(context=context)

        context_description_node, _ = NeoContextDescription.get_or_create(context_description=context_description, context_node=context_node)

        context_node.set_relationships(term_node=term_node, alias_node=alias_node, definition_node=definition_node, context_description_node=context_description_node)
        term_node.set_relationships(alias_node=alias_node, definition_node=definition_node, context_node=context_node)
        if alias_node:
            alias_node.set_relationships(term_node=term_node, context_node=context_node)
        definition_node.set_relationships(term_node, context_node, context_description_node)
        context_description_node.set_relationships(definition_node, context_node)
        
    except Exception as e: 
        logger.error(f"Error in run_unique_definition_creation: {e}")
        raise e
    
def run_duplicate_definition_creation(alias, definition, context, context_description):
    try:

        alias_node = None
        alias__ = False
        if alias:
            alias_node, _ = NeoAlias.get_or_create(alias=alias)
            logger.info(f"Alias Node: {alias_node}")

        context_node, _ = NeoContext.get_or_create(context=context)
        logger.info(f"Context Node: {context_node}")
        context_description_node, _ = NeoContextDescription.get_or_create(context_description=context_description, context_node=context_node)
        logger.info(f"Context Description Node: {context_description_node}")

        definition_node, _ = NeoDefinition.get_or_create(definition=definition)
        term_node = definition_node.term.single()
        if not term_node:
            context_node.alias.connect(alias_node)
            context_node.context_description.connect(context_description_node)
            context_node.definition.connect(definition_node)
            alias_node.context.connect(context_node)
            alias_node.collided_definition.connect(definition_node)
            definition_node.context.connect(context_node)
            definition_node.context_description.connect(context_description_node)
            return
        context_node.set_relationships(term_node=term_node, alias_node=alias_node, definition_node=definition_node, context_description_node=context_description_node)
        logger.info(f"Context Node Relationships: {context_node}")
        logger.info(f"Alias Node Relationships: {alias_node}")
        term_node.set_relationships(alias_node=alias_node, definition_node=definition_node, context_node=context_node)
        if alias_node:
            alias_node.set_relationships(term_node, context_node)
        definition_node.set_relationships(term_node, context_node, context_description_node)

    except Exception as e: 
        logger.error(f"Error in run_duplicate_definition_creation: {e}")
        raise e

def run_collision_definition_creation(alias, most_similar_definition, definition, context, context_description, definition_vector_embedding, highest_score):
    try:
        alias_node = None
        if alias:
            alias_node, _ = NeoAlias.get_or_create(alias=alias)
        existing_definition_node = NeoDefinition.nodes.get(definition=most_similar_definition)
        colliding_definition_node = NeoDefinition(definition=definition, embedding=definition_vector_embedding)
        colliding_definition_node.save()
        context_node, _ = NeoContext.get_or_create(context=context)
        
        context_description_node, _ = NeoContextDescription.get_or_create(context_description=context_description, context_node=context_node)

        alias_node.context.connect(context_node)
        context_node.context_description.connect(context_description_node)
        context_node.definition.connect(colliding_definition_node)
        context_description_node.definition.connect(colliding_definition_node)
        colliding_definition_node.context.connect(context_node)
        colliding_definition_node.context_description.connect(context_description_node)
        alias_node.collided_definition.connect(colliding_definition_node)
        colliding_definition_node.collision_alias.connect(alias_node)
        colliding_definition_node.collision.connect(existing_definition_node)

    except Exception as e: 
        logger.error(f"Error in run_collision_definition_creation: {e}")
        raise e


