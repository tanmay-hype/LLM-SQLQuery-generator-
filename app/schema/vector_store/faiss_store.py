import os

import faiss
import numpy as np

from app.schema.models.schema_document import SchemaDocument
from app.schema.models.semantic_match import SemanticMatch
from app.schema.vector_store.base import BaseVectorStore


class FAISSVectorStore(BaseVectorStore):
    """
    FAISS-backed vector store for semantic schema retrieval.
    """

    def __init__(self):
        self.index = None
        self.documents: list[SchemaDocument] = []

    def add(
        self,
        documents: list[SchemaDocument],
        embeddings: list[list[float]],
    ) -> None:
        """
        Build the FAISS index from embeddings.
        """

        if not embeddings:
            raise ValueError("No embeddings were provided.")

        vectors = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        faiss.normalize_L2(vectors)

        dimension = vectors.shape[1]

        self.index = faiss.IndexFlatIP(dimension)

        self.index.add(vectors)

        self.documents = documents

    def search(
        self,
        embedding: list[float],
        top_k: int,
    ) -> list[SemanticMatch]:
        """
        Search the vector store.
        """

        if self.index is None:
            raise RuntimeError(
                "Vector index has not been initialized."
            )

        vector = np.asarray(
            [embedding],
            dtype=np.float32,
        )

        faiss.normalize_L2(vector)

        scores, indices = self.index.search(
            vector,
            top_k,
        )

        matches: list[SemanticMatch] = []

        for score, idx in zip(scores[0], indices[0]):

            if idx == -1:
                continue

            matches.append(
                SemanticMatch(
                    document=self.documents[idx],
                    score=float(score),
                )
            )

        return matches

    def save(
        self,
        path: str,
    ) -> None:
        """
        Save the FAISS index to disk.
        """

        if self.index is None:
            raise RuntimeError(
                "No FAISS index to save."
            )

        faiss.write_index(
            self.index,
            path,
        )

    def load(
        self,
        path: str,
    ) -> None:
        """
        Load a FAISS index from disk.
        """

        if not os.path.exists(path):
            raise FileNotFoundError(path)

        self.index = faiss.read_index(path)

    def exists(
        self,
        path: str,
    ) -> bool:
        """
        Check whether a persisted index exists.
        """

        return os.path.exists(path)