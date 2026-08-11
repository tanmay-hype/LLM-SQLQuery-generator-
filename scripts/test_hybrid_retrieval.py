from app.core.database import engine
from app.core.config import settings

from app.schema.schema_loader import SchemaLoader
from app.schema.schema_document_builder import SchemaDocumentBuilder

from app.schema.embeddings.gemini_embedding_service import (
    GeminiEmbeddingService,
)

from app.schema.vector_store.faiss_store import FAISSVectorStore

from app.schema.indexing.schema_index_service import (
    SchemaIndexService,
)

from app.schema.retrievers.keywords_retriever import (
    KeywordRetriever,
)

from app.schema.retrievers.semantic_retriever import (
    SemanticRetriever,
)

from app.schema.schema_retriever import SchemaRetriever


def main():

    print("\n" + "=" * 60)
    print("HYBRID RETRIEVAL TEST")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Load database schema
    # --------------------------------------------------

    print("\n[1] Loading database schema...")

    loader = SchemaLoader(engine)

    schema = loader.load_schema()

    print(
        f"Tables found: {list(schema.keys())}"
    )

    # --------------------------------------------------
    # 2. Build schema documents
    # --------------------------------------------------

    print("\n[2] Building schema documents...")

    document_builder = SchemaDocumentBuilder()

    documents = document_builder.build(
        schema
    )

    print(
        f"Documents created: {len(documents)}"
    )

    for document in documents:
        print(f"- {document.table_name}")

    # --------------------------------------------------
    # 3. Initialize embedding service
    # --------------------------------------------------

    print("\n[3] Initializing Gemini embedding service...")

    embedding_service = GeminiEmbeddingService()

    print(
        f"Embedding model: "
        f"{settings.gemini_embedding_model}"
    )

    # --------------------------------------------------
    # 4. Initialize FAISS
    # --------------------------------------------------

    print("\n[4] Initializing FAISS vector store...")

    vector_store = FAISSVectorStore()

    # --------------------------------------------------
    # 5. Initialize schema index
    # --------------------------------------------------

    print("\n[5] Initializing schema index service...")

    index_service = SchemaIndexService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    index_service.initialize(
        documents
    )

    print("Semantic index initialized successfully.")

    # --------------------------------------------------
    # 6. Create retrievers
    # --------------------------------------------------

    print("\n[6] Creating hybrid retrievers...")

    keyword_retriever = KeywordRetriever()

    semantic_retriever = SemanticRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    schema_retriever = SchemaRetriever(
        retrievers=[
            keyword_retriever,
            semantic_retriever,
        ]
    )

    print("Keyword retriever: OK")
    print("Semantic retriever: OK")
    print("RRF fusion: OK")

    # --------------------------------------------------
    # 7. Test questions
    # --------------------------------------------------

    questions = [
        "Which table stores buyer details?",
        "Show customer names and email addresses",
        "Which products were ordered?",
        "Show orders placed by customers",
    ]

    # --------------------------------------------------
    # 8. Run hybrid retrieval
    # --------------------------------------------------

    for question in questions:

        print("\n" + "-" * 60)
        print(f"Question: {question}")
        print("-" * 60)

        results = schema_retriever.retrieve(
            schema=schema,
            question=question,
            documents=documents,
        )

        print("\nSelected tables:")

        for table_name in results:
            print(f"  - {table_name}")

    print("\n" + "=" * 60)
    print("HYBRID RETRIEVAL TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

