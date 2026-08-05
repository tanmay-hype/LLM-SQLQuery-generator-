from app.schema.embeddings.embedding_service import EmbeddingService
from app.schema.vector_store.base import BaseVectorStore
from app.schema.models.schema_document import SchemaDocument

class SchemaIndexService:
    """
    Service responsible for indexing schema documents into a vector store.
    """

    def __init__(self, embedding_service: EmbeddingService, vecotr_store: BaseVectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vecotr_store
    
    def index(self, documents: list[SchemaDocument]):
        """
        Indexes the given schema documents into the vector store.
        """
        texts = [document.content for document in documents]
        embeddings = self.embedding_service.embed(texts)
        self.vector_store.index(documents, embeddings)
    
    def search(self, question: str, top_k: int) -> list[SchemaDocument]:
    
        embedding = self.embedding_service.embed([question])[0]
        return self.vector_store.search(embedding, top_k)
    