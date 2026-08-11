from app.core.database import engine

from app.schema.schema_loader import SchemaLoader
from app.schema.schema_document_builder import SchemaDocumentBuilder

from app.schema.embeddings.gemini_embedding_service import (
    GeminiEmbeddingService,
)

from app.schema.vector_store.faiss_store import FAISSVectorStore

from app.schema.indexing.schema_index_service import (
    SchemaIndexService,
)

from app.core.config import settings


def main():
    print("=" * 60)
    print("SEMANTIC RETRIEVAL TEST")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Load database schema
    # --------------------------------------------------

    print("\n[1] Loading database schema...")

    loader = SchemaLoader(engine)

    schema = loader.load_schema()

    print(f"Tables found: {list(schema.keys())}")

    if not schema:
        raise RuntimeError(
            "No tables were found in the database."
        )

    # --------------------------------------------------
    # 2. Build schema documents
    # --------------------------------------------------

    print("\n[2] Building schema documents...")

    document_builder = SchemaDocumentBuilder()

    documents = document_builder.build(schema)

    print(f"Documents created: {len(documents)}")

    for document in documents:
        print(
            f"  - {document.table_name}"
        )

    # --------------------------------------------------
    # 3. Create embedding service
    # --------------------------------------------------

    print("\n[3] Initializing Gemini embedding service...")

    embedding_service = GeminiEmbeddingService()

    print(
        f"Embedding model: "
        f"{settings.gemini_embedding_model}"
    )

    # --------------------------------------------------
    # 4. Create FAISS vector store
    # --------------------------------------------------

    print("\n[4] Initializing FAISS vector store...")

    vector_store = FAISSVectorStore()

    # --------------------------------------------------
    # 5. Create schema index service
    # --------------------------------------------------

    print("\n[5] Initializing schema index service...")

    index_service = SchemaIndexService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    # --------------------------------------------------
    # 6. Build/load index
    # --------------------------------------------------

    print("\n[6] Initializing semantic index...")

    index_service.initialize(documents)

    print("Semantic index initialized successfully.")

    print(
        f"FAISS index path: "
        f"{settings.faiss_index_path}"
    )

    print(
        f"Metadata path: "
        f"{settings.schema_metadata_path}"
    )

    # --------------------------------------------------
    # 7. Semantic search
    # --------------------------------------------------

    question = (
        #Which table contains customer information?"
        "Which table stores buyer details?"
        #Which table contains items available for sale?"
    )

    print("\n[7] Running semantic search...")

    print(f"Question: {question}")

    results = index_service.search(
        question=question,
        top_k=3,
    )

    # --------------------------------------------------
    # 8. Display results
    # --------------------------------------------------

    print("\n[8] Search results")
    print("-" * 60)

    if not results:
        print("No semantic matches found.")
        return

    for position, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"{position}. "
            f"{result.document.table_name}"
        )

        print(
            f"   Score: {result.score:.4f}"
        )

        print(
            f"   Content: "
            f"{result.document.content}"
        )

        print()

    print("=" * 60)
    print("SEMANTIC RETRIEVAL TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

