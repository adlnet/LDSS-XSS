from django.shortcuts import render

from sentence_transformers import SentenceTransformer
import numpy as np


def single_term_comparision(term: str, definition: str):
    # does a duplicate exist? does

    try:

        model = SentenceTransformer('all-mpnet-base-v2')


        term_vector_embedding = model.encode(term, convert_to_numpy=True)
        definition_vector_embedding = model.encode(definition, convert_to_numpy=True)
    #getting all term nodes from neo4j and then turning them into vectors and storing them temporarily?

    #as nodes are added, store them in neo4j but also as vectors in elasticsearch if so how do we tie that vector to a neo4j UID


def normalize_embedding(embedding):

    norm = np.linalg.norm(embedding, axis=1)




