from elasticsearch import Elasticsearch, exceptions
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger('dict_config_logger')


class ElasticsearchClient:
    def __init__(self, host='localhost', port=9200, model_name='all-mpnet-base-v2'):
        self.host = host
        self.port = port
        self.es = None
        self.model = SentenceTransformer(model_name)

    def connect(self):
        """
        Connects to the Elasticsearch Docker container.
        """
        self.es = Elasticsearch([{'host': self.host, 'port': self.port}])
        try:
            if not self.es.ping():
                raise ValueError("Connection failed")
        except exceptions.ConnectionError as e:
            print(f"Elasticsearch connection failed: {e}")
    
    def disconnect(self):
        """
        Closes the connection to Elasticsearch.
        """
        if self.es is not None:
            self.es.transport.close()
            self.es = None

    def ensure_index(self, index_name='xss_index', vector_dim=384):
        """
        Ensures that the Elasticsearch index is set up properly with the correct mappings.
        """
        if not self.es.indices.exists(index=index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "uid": {
                            "type": "keyword"
                        },
                        "term": {
                            "type": "text"
                        },
                        "definition": {
                            "type": "text"
                        },
                        "term_embedding": {
                            "type": "dense_vector",
                            "dims": vector_dim,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "definition_embedding": {
                            "type": "dense_vector",
                            "dims": vector_dim,
                            "index": True,
                            "similarity": "cosine"
                        }
                    }
                }
            }
            self.es.indices.create(index=index_name, body=mapping)

    def create_embedding(self, term):
        """
        Creates a vector embedding for the given text using SentenceTransformer.
        """
        definition_embedding = self.model.encode(term.definition)
        term_embedding = self.model.encode(term.term)
        return definition_embedding, term_embedding

    def index_document(self, index_name, term, definition, uid):
        """
        Indexes a document with its term, definition, uid, and embedding into Elasticsearch.
        """
        embeddings = self.create_embedding(term,definition)
        doc = {
            'uid': uid,
            'term': term,
            'definition': definition,
            'term_embedding': embeddings['term_embedding'],
            'definition_embedding': embeddings['definition_embedding']
        }
        self.es.index(index=index_name, body=doc)

    def check_similarity(self, index_name, term_embedding, definition_embedding, k=5):
        """
        Checks if a vector embedding is similar to any existing embeddings in the database.
        """
        term_query = {
            "knn": {
                "field": "term_embedding",
                "query_vector": term_embedding,
            }
        }
        return response['hits']['hits']

    def search_by_uid(self, index_name, uid):
        """
        Retrieves a document from Elasticsearch by its UID.
        """
        query = {
            "term": {
                "uid": uid
            }
        }
        response = self.es.search(index=index_name, body={"query": query})
        return response['hits']['hits']

