from .models import NeoAlias, NeoDefinition, NeoContext, NeoContextDescription, NeoTerm
from deconfliction_service.views import run_deconfliction
import logging
from uuid import uuid4
logger = logging.getLogger('dict_config_logger')

def run_node_creation(alias: str, definition: str, context: str, context_description: str):
    try:
        logger.info('Running Deconfliction')
        definition_vector_embedding, deconfliction_status, most_similar_text, highest_score = run_deconfliction(alias, definition, context, context_description)
        logger.info(f'Highest score: {highest_score}')
        logger.info('Deconfliction complete')
        logger.info(f'Deconfliction result: {deconfliction_status}')
        
        if deconfliction_status == 'unique':
            run_unique_definition_creation(alias, definition, context, context_description, definition_vector_embedding)
        elif deconfliction_status == 'duplicate':
            alias_created, context_created, context_description_created = run_duplicate_definition_creation(alias, most_similar_text, context, context_description)
            return alias_created, context_created, context_description_created
        elif deconfliction_status == 'collision':
            run_collision_definition_creation(alias, most_similar_text, definition, context, context_description, definition_vector_embedding, highest_score)
            

    except Exception as e: 
        logger.error(f"Error in run_node_creation: {e}")
        raise e


def run_unique_definition_creation(alias, definition, context, context_description, definition_vector_embedding):
    try:
        uid = uuid4()

        term_node = NeoTerm(uid=uid)
        term_node.save()

        alias_node, created = NeoAlias.get_or_create(alias=alias)
        definition_node = NeoDefinition(definition=definition, embedding=definition_vector_embedding)
        definition_node.save()
        logger.info(f"Definition node created: {definition_node}")
        context_node, created = NeoContext.get_or_create(context=context)
        existing_context_description = context_node.context_description.all()
        if existing_context_description:
            context_description_node = existing_context_description[0]
        else:
            context_description_node, created = NeoContextDescription.get_or_create(context_description=context_description)

        context_node.set_relationships(term_node, alias_node, definition_node, context_description_node)
        term_node.set_relationships(alias_node, definition_node, context_node)
        alias_node.set_relationships(term_node, context_node)
        definition_node.set_relationships(term_node, context_node, context_description_node)
        context_description_node.set_relationships(definition_node, context_node)
        
    except Exception as e: 
        logger.error(f"Error in run_unique_definition_creation: {e}")
        raise e
    
def run_duplicate_definition_creation(alias, definition, context, context_description):
    try:
        alias_node, alias_created = NeoAlias.get_or_create(alias=alias)

        context_node, context_created = NeoContext.get_or_create(context=context)
        existing_context_description = context_node.context_description.all()
        if existing_context_description:
            context_description_node = existing_context_description[0]
            context_description_created = False
        else:
            context_description_node, context_description_created = NeoContextDescription.get_or_create(context_description=context_description)

        definition_node = NeoDefinition.nodes.get(definition=definition)
        term_node = definition_node.term.single()
        if not term_node:
            context_node.alias.connect(alias_node)
            context_node.context_description.connect(context_description_node)
            context_node.definition.connect(definition_node)
            alias_node.context.connect(context_node)
            alias_node.collided_definition.connect(definition_node)
            definition_node.context.connect(context_node)
            definition_node.context_description.connect(context_description_node)
            return alias_created, context_created, context_description_created
        context_node.set_relationships(term_node, alias_node, definition_node, context_description_node)
        term_node.set_relationships(alias_node, definition_node, context_node)
        alias_node.set_relationships(term_node, context_node)
        definition_node.set_relationships(term_node, context_node, context_description_node)

        return alias_created, context_created, context_description_created

        pass
    except Exception as e: 
        logger.error(f"Error in run_duplicate_definition_creation: {e}")
        raise e

def run_collision_definition_creation(alias, most_similar_definition, definition, context, context_description, definition_vector_embedding, highest_score):
    try:
        alias_node, alias_created = NeoAlias.get_or_create(alias=alias)
        existing_definition_node = NeoDefinition.nodes.get(definition=most_similar_definition)
        colliding_definition_node = NeoDefinition(definition=definition, embedding=definition_vector_embedding)
        colliding_definition_node.save()
        context_node, context_created = NeoContext.get_or_create(context=context)
        existing_context_description = context_node.context_description.all()
        if existing_context_description:
            context_description_node = existing_context_description[0]
        else:
            context_description_node, context_description_created = NeoContextDescription.get_or_create(context_description=context_description)

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