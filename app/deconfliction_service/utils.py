from elasticsearch import Elasticsearch, exceptions
from sentence_transformers import SentenceTransformer
import logging
import numpy as np

logger = logging.getLogger('dict_config_logger')


class ElasticsearchClient:
    def __init__(self, host='elasticsearch', port=9200, model_name='all-mpnet-base-v2', scheme="http"):
        self.host = host
        self.port = port
        self.es = None
        self.scheme = scheme
        self.model = SentenceTransformer(model_name)

    def connect(self):
        """
        Connects to the Elasticsearch Docker container.
        """
        self.es = Elasticsearch([{'host': self.host, 'port': self.port, 'scheme': self.scheme}])
        try:
            if not self.es.ping():
                raise ValueError("Connection failed")
        except exceptions.ConnectionError as e:
            print(f"Elasticsearch connection failed: {e}")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise e
    
    def disconnect(self):
        """
        Closes the connection to Elasticsearch.
        """
        if self.es is not None:
            self.es.transport.close()
            self.es = None

    def ensure_index(self, index_name='xss1_index', vector_dim=768):
        """
        Ensures that the Elasticsearch index is set up properly with the correct mappings.
        """
        try:

            if not self.es.indices.exists(index=index_name):
                mapping = {
                    "mappings": {
                        "properties": {
                            "uid": {
                                "type": "keyword"
                            },
                        
                            "definition": {
                                "type": "text"
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
                logger.info(f"Index {index_name} created successfully.")
        except exceptions.BadRequestError as e:
            logger.error(f"The request body mapping is invalid: {e}")
        except exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except exceptions.ConflictError as e:
            logger.error(f"Index already exists: {e}")
        except exceptions.TransportError as e:
            logger.error(f"Transport error: {e}")
            

    def create_embedding(self, definition):
        """
        Creates a vector embedding for the given text using SentenceTransformer.
        """
        definition_embedding = self.model.encode(definition)

        norm = np.linalg.norm(definition_embedding)

        if norm > 0:
            definition_embedding = definition_embedding / norm

        return definition_embedding
    
    def index_document(self, index_name, definition_embedding, lcvid):
        """
        Indexes a document with its term, definition, uid, and embedding into Elasticsearch.
        """
        # logger.info(f'definition_embedding length: {len(definition_embedding)}')
        # logger.info(f'index_name: {index_name}')
        doc = {
            'lcvid': lcvid,
            'definition_embedding': definition_embedding,
        }
        self.es.index(index=index_name, body=doc)

    def check_similarity(self, definition_embedding, index_name='xss1_index', k=5, expected_dim=768, def_threshold_low=0.50, def_threshold_high=0.95):
        """
        Checks if a vector embedding is similar to any existing embeddings in the database.
        """

        def is_deviation(def_score, most_similar_def_lcvid): #one term(lcvid) has multiple definitions
            return def_score <= def_threshold_low #and most_similar_def_lcvid == lcvid

        def is_duplication(def_score):
            return def_score > def_threshold_high #and comparison_lcvid == lcvid

        def is_collision(def_score):
            return def_threshold_low < def_score <= def_threshold_high
                    #0.50 < 0.92 <= 0.95
        def find_existing(hits, most_similar, field):
            for hit in hits:
                if hit['_source'][field] == most_similar:
                    return hit['_source']
            return None

        try:
            # Check that the query vector has the correct dimensions
            if len(definition_embedding) != expected_dim:
                raise ValueError(f"Query vector dimension mismatch: Expected {expected_dim}, got {len(definition_embedding)}")


            # Prepare the k-NN query
            definition_query = {
                "knn": {
                    "field": "definition_embedding",
                    "query_vector": definition_embedding,
                    "k": k,
                    "num_candidates": 1000,
                }
            }

            # Execute the search
            definition_response = self.es.search(index=index_name, body={"query": definition_query})
            definition_hits = definition_response['hits']['hits']
        
            if definition_hits:
                definition_hit = definition_hits[0]  # Most similar definition match
                logger.info(f"Definition hit: {definition_hit}")
                def_score = definition_hit['_score']
                logger.info(f"Definition score: {def_score}")

                most_similar_def_lcvid = definition_hit['_source']['lcvid']


                # Check for each case using the helper functions
                if is_deviation(def_score, most_similar_def_lcvid):
                    return {
                        "type": "deviation",
                        "existingTerm": find_existing(definition_hits, most_similar_def_lcvid, "lcvid")
                    }
                elif is_duplication(def_score):
                    return {
                        "type": "duplication",
                        "existingTerm": find_existing(definition_hits, most_similar_def_lcvid, "lcvid")
                    }
                elif is_collision(def_score):
                    return {
                        "type": "collision",
                        "existingTerm": find_existing(definition_hits, most_similar_def_lcvid, "lcvid")
                    }
                else:
                    return {
                        "type": "unique",
                        "existingTerm": None
                    }
            else:
                # If no valid hits were found, treat it as unique
                return {
                    "type": "unique",
                    "existingTerm": None
                }
            
        except ValueError as e:
            # Handle dimension mismatch in query vector
            logger.error(f"Dimension mismatch error: {e}")
            raise e

        except exceptions.BadRequestError as e:
            # Handle issues with the query structure or field names
            logger.error(f"BadRequestError during search: {e}")
            if "different number of dimensions" in str(e):
                logger.error("Dimension mismatch between query vector and index vectors. Check vector dimensions.")
            raise e

        except exceptions.ConnectionError as e:
            # Handle connectivity issues with Elasticsearch
            logger.error(f"ConnectionError: Could not connect to Elasticsearch - {e}")
            raise e

        except exceptions.TransportError as e:
            # General error for various transport issues
            logger.error(f"TransportError during search: {e}")
            raise e

        except Exception as e:
            # Catch-all for any other exceptions
            logger.error(f"An unexpected error occurred: {e}")
            raise e
    
    # def check_similarity(self, definition_embedding, index_name='xss1_index', k=5):
    #     """
    #     Checks if a vector embedding is similar to any existing embeddings in the database.
    #     """
    #     definition_query = {
    #         "knn": {
    #             "field": "definition_embedding",
    #             "query_vector": definition_embedding,
    #             "k": k,
    #             "num_candidates": 1000,
    #         }
    #     }

    #     definition_response = self.es.search(index=index_name, body={"query": definition_query})
    #     definition_hits = definition_response['hits']['hits']

    #     logger.info(f"Definition similarity search response: {definition_hits}")


    #     if definition_hits:
    #         definition_hit = definition_hits[0]  # Most similar definition match
    #         def_score = definition_hit['_score']
    #         most_similar_def = definition_hit['_source']['definition']

    #     # Check for each case using separate functions
    #         if self.is_deviation(def_score, def_threshold_low):
    #             return {
    #             "type": "deviation",
    #             "existingTerm": self.find_existing(definition_hits, most_similar_def, "definition")
    #         }
    #         elif self.is_duplication(def_score, def_threshold_high):
    #             return {
    #             "type": "duplication",
    #             "existingTerm": self.find_existing(definition_hits, most_similar_def, "definition")
    #             }
    #         elif self.is_collision(def_score, def_threshold_high):
    #             return {
    #             "type": "collision",
    #             "existingTerm": self.find_existing(definition_hits, most_similar_def, "definition")
    #             }
    #         else:
    #             return {
    #             "type": "unique",
    #             "existingTerm": None
    #             }
    #     else:
    #         # If no valid hits were found, treat it as unique
    #         return {
    #             "type": "unique",
    #             "existingTerm": None
    #         }

    # Separate functions for checking each case
    def is_deviation(self, def_score, def_threshold_low):
        """
        Checks if the case is a deviation (low similarity score for definition).
        """
        return def_score <= def_threshold_low

    def is_duplication(self, def_score, def_threshold_high):
        """
        Checks if the case is a duplication (high similarity score for definition).
        """
        return def_score > def_threshold_high

    def is_collision(self, def_score, def_threshold_high):
        """
        Checks if the case is a collision (moderate similarity score for definition).
        """
        return def_threshold_low < def_score <= def_threshold_high

    def find_existing(self, hits, most_similar, field):
        """
        Helper function to find the existing document in the database
        based on the most similar definition.
        """
        for hit in hits:
            if hit['_source'][field] == most_similar:
                return hit['_source']
        return None 

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

