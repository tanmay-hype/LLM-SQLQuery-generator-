import os
from pathlib import Path

import faiss
import numpy as np

from app.schema.models.schema_document import SchemaDocument
from app.schema.models.semantic_match import SemanticMatch
from app.schema.persistence.metadata_store import MetadataStore
from app.schema.vector_store.base import BaseVectorStore


class FAISSVectorStore(BaseVectorStore):
    """
    FAISS-backed vector store for semantic schema retrieval.
    """

    def __init__(self):
        self.index = None
        self.documents: list[SchemaDocument] = []
        self.metadata_store = MetadataStore()

    def add(
        self,
        documents: list[SchemaDocument],
        embeddings: list[list[float]],
    ) -> None:
        """
        Build the FAISS index from document embeddings.
        """

        if not documents:
            raise ValueError(
                "No documents were provided."
            )

        if not embeddings:
            raise ValueError(
                "No embeddings were provided."
            )

        if len(documents) != len(embeddings):
            raise ValueError(
                "Number of documents does not match "
                "number of embeddings."
            )

        vectors = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        if vectors.ndim != 2:
            raise ValueError(
                "Embeddings must be a 2-dimensional array."
            )

        # Normalize vectors so inner product becomes
        # cosine similarity.
        faiss.normalize_L2(vectors)

        dimension = vectors.shape[1]

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(vectors)

        self.documents = list(documents)

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

        if not self.documents:
            return []

        if top_k <= 0:
            return []

        top_k = min(
            top_k,
            len(self.documents),
        )

        vector = np.asarray(
            [embedding],
            dtype=np.float32,
        )

        if vector.ndim != 2:
            raise ValueError(
                "Query embedding must be a 1-dimensional vector."
            )

        faiss.normalize_L2(vector)

        scores, indices = self.index.search(
            vector,
            top_k,
        )

        matches: list[SemanticMatch] = []

        for score, idx in zip(
            scores[0],
            indices[0],
        ):
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
        index_path: str,
        metadata_path: str,
    ) -> None:
        """
        Persist the FAISS index and document metadata.
        """

        if self.index is None:
            raise RuntimeError(
                "No FAISS index to save."
            )

        Path(index_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        Path(metadata_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            index_path,
        )

        self.metadata_store.save(
            metadata_path,
            self.documents,
        )

    def load(
        self,
        index_path: str,
        metadata_path: str,
    ) -> None:
        """
        Load a persisted FAISS index and metadata.
        """

        if not os.path.exists(index_path):
            raise FileNotFoundError(
                f"FAISS index file not found at {index_path}"
            )

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(
                f"Metadata file not found at {metadata_path}"
            )

        self.index = faiss.read_index(
            index_path
        )

        self.documents = self.metadata_store.load(
            metadata_path
        )

        if self.index.ntotal != len(self.documents):
            raise ValueError(
                "FAISS index size does not match "
                "number of stored documents."
            )

    def exists(
        self,
        index_path: str,
        metadata_path: str,
    ) -> bool:
        """
        Return True if both persisted files exist.
        """

        return (
            os.path.exists(index_path)
            and os.path.exists(metadata_path)
        )

