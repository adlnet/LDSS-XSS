from elasticsearch import Elasticsearch, ConnectionError
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger('dict_config_logger')

def get_elastic_search_connection():
    try:
        es = Elasticsearch(
        hosts=[{'host': 'elasticsearch', 'port':9200, 'scheme': 'http'}],
        timeout=30,
        max_retries=10,
        retry_on_timeout=True,

        )
    except ConnectionError as e:
        logger.Error('Error connecting to elasticsearch')
        return
    return es