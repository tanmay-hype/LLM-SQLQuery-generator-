import faiss
import numpy as np

from app.schema.models.schema_document import SchemaDocument
from app.schema.models.semantic_match import SemanticMatch
from app.schema.vector_store.base import BaseVectorStore


class FAISSVectorStore(BaseVectorStore):
    """
    FAISS-backed vector store for schema documents.
    """

    def __init__(self):
        self.index = None
        self.documents: list[SchemaDocument] = []

    def index(
        self,
        documents: list[SchemaDocument],
        embeddings: list[list[float]],
    ):
        """
        Build the FAISS index.
        """

        if not embeddings:
            raise ValueError("No embeddings were provided.")

        vectors = np.array(
            embeddings,
            dtype=np.float32,
        )

        # Normalize vectors so inner product = cosine similarity
        faiss.normalize_L2(vectors)

        dimension = vectors.shape[1]

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(vectors)

        self.documents = documents

    def search(
        self,
        embedding: list[float],
        top_k: int,
    ) -> list[SemanticMatch]:
        """
        Retrieve the most similar schema documents.
        """

        if self.index is None:
            raise RuntimeError(
                "Vector index has not been built."
            )

        vector = np.array(
            [embedding],
            dtype=np.float32,
        )

        faiss.normalize_L2(vector)

        scores, indices = self.index.search(
            vector,
            top_k,
        )

        results = []

        for score,idx in zip(scores[0], indices[0]):

            if idx == -1:
                continue

            results.append(
                SemanticMatch(
                    document=self.documents[idx],
                    score = float(score)
                )
            )

        return results