from app.schema.embeddings.embedding_service import EmbeddingService
from app.schema.vector_store.base import BaseVectorStore
from app.schema.models.schema_document import SchemaDocument
from app.settings import settings

class SchemaIndexService:
    """
    Service responsible for indexing schema documents into a vector store.
    """

    def __init__(self, embedding_service: EmbeddingService, vector_store: BaseVectorStore):
        self._initialized = False
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    def add(self, documents: list[SchemaDocument]) ->None:
        """
        Indexes the given schema documents into the vector store.
        """
        texts = [document.content for document in documents]
        embeddings = self.embedding_service.create_embeddings(texts)
        self.vector_store.add(documents, embeddings)
    
    def search(self, question: str, top_k: int) -> list[SchemaDocument]:

        embedding = self.embedding_service.create_embeddings([question])[0]
        return self.vector_store.search(embedding, top_k)
    
    def initialize(self, documents: list[SchemaDocument])-> None:
        """
        Initializes the index service by indexing the provided schema documents.
        """
        if self.vector_store.exists(
            settings.faiss_index_path,
            settings.schema_metadata_path,
        ):
            self.vector_store.load(
                settings.faiss_index_path,
                settings.schema_metadata_path,
            )
            
            return 
        self.build(documents)
        
        self.vector_store.save(
            settings.faiss_index_path,
            settings.schema_metadata_path,
        )

    def build(self, documents: list[SchemaDocument]) -> None:
        
        texts = [document.content for document in documents]
        
        embeddings = self.embedding_service.create_embeddings(texts)
        
        self.vector_store.add(documents, embeddings)
        

 