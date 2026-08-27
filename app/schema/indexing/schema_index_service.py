import logging

from app.core.config import settings

from app.schema.embeddings.base import (
    EmbeddingService,
)
from app.schema.indexing.schema_fingerprint import (
    SchemaFingerprint,
)
from app.schema.models.schema_document import (
    SchemaDocument,
)
from app.schema.models.semantic_match import (
    SemanticMatch,
)
from app.schema.persistence.metadata_store import (
    MetadataStore,
)
from app.schema.vector_store.base import (
    BaseVectorStore,
)


logger = logging.getLogger(__name__)


class SchemaIndexService:
    """
    Service responsible for creating, loading, persisting,
    validating, and searching the schema vector index.

    The service automatically detects schema changes using
    deterministic schema fingerprints.

    Lifecycle:

        Current schema documents
                ↓
        Generate fingerprint
                ↓
        Persisted index exists?
             /          \\
           No            Yes
           ↓              ↓
        Build        Compare fingerprints
                         /        \\
                      Same       Different
                       ↓             ↓
                     Load          Rebuild
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
    ):
        self.embedding_service = (
            embedding_service
        )

        self.vector_store = (
            vector_store
        )

        self.metadata_store = (
            MetadataStore()
        )

        self._initialized = False

        self._schema_fingerprint: str | None = (
            None
        )

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def initialize(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Initialize the semantic schema index.

        Behavior:

        1. Calculate the current schema fingerprint.
        2. If the already-loaded index has the same
           fingerprint, return immediately.
        3. If persisted index files exist, compare their
           schema fingerprint with the current schema.
        4. Load the index when fingerprints match.
        5. Rebuild the index when fingerprints differ.
        """

        if not documents:
            raise ValueError(
                "Cannot initialize schema index "
                "without documents."
            )

        current_fingerprint = (
            SchemaFingerprint.create(
                documents
            )
        )

        # --------------------------------------------------
        # Already initialized with this exact schema.
        # --------------------------------------------------

        if (
            self._initialized
            and self._schema_fingerprint
            == current_fingerprint
        ):
            return

        index_path = (
            settings.faiss_index_path
        )

        metadata_path = (
            settings.schema_metadata_path
        )

        # ==================================================
        # PERSISTED INDEX EXISTS
        # ==================================================

        if self.vector_store.exists(
            index_path,
            metadata_path,
        ):

            try:

                persisted_fingerprint = (
                    self.metadata_store.fingerprint(
                        metadata_path
                    )
                )

                # ------------------------------------------
                # Schema unchanged
                # ------------------------------------------

                if (
                    persisted_fingerprint
                    == current_fingerprint
                ):

                    logger.info(
                        "Schema unchanged. "
                        "Loading persisted FAISS index."
                    )

                    self.vector_store.load(
                        index_path,
                        metadata_path,
                    )

                    self._initialized = True

                    self._schema_fingerprint = (
                        current_fingerprint
                    )

                    return

                # ------------------------------------------
                # Schema changed
                # ------------------------------------------

                logger.info(
                    "Database schema change detected. "
                    "Rebuilding FAISS index."
                )

            except Exception as exc:

                # Corrupt or incompatible metadata should not
                # permanently prevent index initialization.
                logger.warning(
                    "Unable to validate persisted schema "
                    "metadata. Rebuilding index. Error: %s",
                    exc,
                )

        else:

            logger.info(
                "No persisted FAISS schema index found. "
                "Building a new index."
            )

        # ==================================================
        # BUILD / REBUILD INDEX
        # ==================================================

        self._build_and_persist(
            documents
        )

        self._initialized = True

        self._schema_fingerprint = (
            current_fingerprint
        )

    # ======================================================
    # BUILD
    # ======================================================

    def build(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Build the vector index from schema documents.
        """

        if not documents:
            raise ValueError(
                "Cannot build schema index "
                "without documents."
            )

        texts = [
            document.content
            for document in documents
        ]

        embeddings = (
            self.embedding_service
            .create_embeddings(
                texts
            )
        )

        if (
            len(embeddings)
            != len(documents)
        ):
            raise ValueError(
                "Number of embeddings does not match "
                "number of schema documents."
            )

        self.vector_store.add(
            documents,
            embeddings,
        )

    # ======================================================
    # BUILD + PERSIST
    # ======================================================

    def _build_and_persist(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Build the complete schema index and persist both
        FAISS vectors and schema metadata.
        """

        logger.info(
            "Building schema vector index..."
        )

        self.build(
            documents
        )

        self.vector_store.save(
            settings.faiss_index_path,
            settings.schema_metadata_path,
        )

        logger.info(
            "Schema vector index built "
            "and persisted successfully."
        )

    # ======================================================
    # ADD
    # ======================================================

    def add(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Add schema documents to the current vector index.

        Note:
            For complete schema-change safety, rebuild()
            remains the preferred operation when the
            database structure changes.
        """

        if not documents:
            return

        texts = [
            document.content
            for document in documents
        ]

        embeddings = (
            self.embedding_service
            .create_embeddings(
                texts
            )
        )

        if (
            len(embeddings)
            != len(documents)
        ):
            raise ValueError(
                "Number of embeddings does not match "
                "number of schema documents."
            )

        self.vector_store.add(
            documents,
            embeddings,
        )

    # ======================================================
    # SEARCH
    # ======================================================

    def search(
        self,
        question: str,
        top_k: int,
    ) -> list[SemanticMatch]:
        """
        Search the vector index using a natural-language
        question.
        """

        if not self._initialized:
            raise RuntimeError(
                "Schema index has not been initialized."
            )

        if not question or not question.strip():
            return []

        embeddings = (
            self.embedding_service
            .create_embeddings(
                [question]
            )
        )

        if not embeddings:
            return []

        return self.vector_store.search(
            embedding=embeddings[0],
            top_k=top_k,
        )

    # ======================================================
    # REBUILD
    # ======================================================

    def rebuild(
        self,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Force a complete schema-index rebuild.

        This can be called manually, but normal initialization
        now detects schema changes automatically.
        """

        if not documents:
            raise ValueError(
                "Cannot rebuild schema index "
                "without documents."
            )

        logger.info(
            "Rebuilding schema vector index..."
        )

        self._build_and_persist(
            documents
        )

        self._schema_fingerprint = (
            SchemaFingerprint.create(
                documents
            )
        )

        self._initialized = True

        logger.info(
            "Schema vector index rebuilt successfully."
        )

    # ======================================================
    # STATE
    # ======================================================

    @property
    def initialized(
        self,
    ) -> bool:
        """
        Return whether the index is initialized.
        """

        return self._initialized

    @property
    def schema_fingerprint(
        self,
    ) -> str | None:
        """
        Return the fingerprint of the currently loaded
        database schema.
        """

        return self._schema_fingerprint