from app.core.config import settings

from app.schema.embeddings.base import EmbeddingService
from app.schema.models.schema_document import SchemaDocument
from app.schema.models.semantic_match import SemanticMatch
from app.schema.vector_store.base import BaseVectorStore


class SchemaIndexService:
    """
    Service responsible for creating, loading, persisting,
    and searching the schema vector index.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self._initialized = False

    def initialize(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Initialize the vector index.

        If a persisted index already exists, load it.
        Otherwise, build the index and persist it.
        """

        if self._initialized:
            return

        if not documents:
            raise ValueError(
                "Cannot initialize schema index without documents."
            )

        index_path = settings.faiss_index_path
        metadata_path = settings.schema_metadata_path

        if self.vector_store.exists(
            index_path,
            metadata_path,
        ):
            self.vector_store.load(
                index_path,
                metadata_path,
            )

            self._initialized = True

            return

        self.build(documents)

        self.vector_store.save(
            index_path,
            metadata_path,
        )

        self._initialized = True

    def build(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Build the vector index from schema documents.
        """

        if not documents:
            raise ValueError(
                "Cannot build schema index without documents."
            )

        texts = [
            document.content
            for document in documents
        ]

        embeddings = (
            self.embedding_service.create_embeddings(
                texts
            )
        )

        if len(embeddings) != len(documents):
            raise ValueError(
                "Number of embeddings does not match "
                "number of schema documents."
            )

        self.vector_store.add(
            documents,
            embeddings,
        )

    def add(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Add new schema documents to the existing vector index.

        This method is intended for incremental indexing.
        """

        if not documents:
            return

        texts = [
            document.content
            for document in documents
        ]

        embeddings = (
            self.embedding_service.create_embeddings(
                texts
            )
        )

        if len(embeddings) != len(documents):
            raise ValueError(
                "Number of embeddings does not match "
                "number of schema documents."
            )

        self.vector_store.add(
            documents,
            embeddings,
        )

    def search(
        self,
        question: str,
        top_k: int,
    ) -> list[SemanticMatch]:
        """
        Search the vector index using a natural-language question.
        """

        if not self._initialized:
            raise RuntimeError(
                "Schema index has not been initialized."
            )

        if not question or not question.strip():
            return []

        embedding = (
            self.embedding_service.create_embeddings(
                [question]
            )[0]
        )

        return self.vector_store.search(
            embedding=embedding,
            top_k=top_k,
        )

    def rebuild(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Rebuild and persist the entire schema index.

        Use this when the database schema changes.
        """

        if not documents:
            raise ValueError(
                "Cannot rebuild schema index without documents."
            )

        self.build(documents)

        self.vector_store.save(
            settings.faiss_index_path,
            settings.schema_metadata_path,
        )

        self._initialized = True

