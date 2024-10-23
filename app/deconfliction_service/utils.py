from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

def get_elastic_search_connection():
    es = Elasticsearch(
        hosts=[{'host': 'elasticsearch', 'port':9200}],
        timeout=30,
        max_retries=10,
        retry_on_timeout=True
    )

    return es