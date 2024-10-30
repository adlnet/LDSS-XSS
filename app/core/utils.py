from .models import NeoAlias, NeoDefinition, NeoContext, NeoContextDescription, NeoTerm
from deconfliction_service.views import run_deconfliction
import logging
from uuid import uuid4
logger = logging.getLogger('dict_config_logger')

def run_node_creation(alias: str, definition: str, context: str, context_description: str):
    try:
        logger.info('Running Deconfliction')
        definition_vector_embedding, deconfliction_status = run_deconfliction(alias, definition, context, context_description)
        logger.info('Deconfliction complete')
        logger.info(f'Deconfliction result: {deconfliction_status}')
        
        if deconfliction_status == 'unique':
            run_unique_definition_creation(alias, definition, context, context_description, definition_vector_embedding)
        elif deconfliction_status == 'duplicate':
            pass
        elif deconfliction_status == 'collision':
            pass

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
        context_node, created = NeoContext.get_or_create(context=context)
        context_description_node, created = NeoContextDescription.get_or_create(context_description=context_description)

        context_node.set_relationships(term_node, alias_node, definition_node, context_description_node)
        term_node.set_relationships(alias_node, definition_node, context_node)
        alias_node.set_relationships(term_node, context_node)
        definition_node.set_relationships(term_node, context_node, context_description_node)
        context_description_node.set_relationships(definition_node,)
        
    except Exception as e: 
        logger.error(f"Error in run_unique_definition_creation: {e}")
        raise e
    
def run_duplicate_definition_creation(alias, definition, context, context_description, definition_vector_embedding):
    try:
        pass
    except Exception as e: 
        logger.error(f"Error in run_duplicate_definition_creation: {e}")
        raise e
