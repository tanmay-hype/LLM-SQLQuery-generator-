import faiss 
import numpy as np

from app.schema.vector_store.base import BaseVectorStore

class FaissVectorStore(BaseVectorStore):
    
    def __init__(self):
        
        self.index = None
        self.documents = []
        
    def index(self, documents, embeddings):
        raise NotImplementedError("Indexing is not implemented yet.")
    
    def search(self, query_embedding, top_k):
        raise NotImplementedError("Searching is not implemented yet.")