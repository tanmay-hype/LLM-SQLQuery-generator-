import os

import faiss
from pathlib import Path
import numpy as np
from app.schema.persistence.metadata_store import MetadataStore
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
        self.metadata_store = MetadataStore()

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
        index_path: str,
        metadata_path: str,
    ) -> None:
        
        Path(index_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.index is None:
            raise RuntimeError(
                "No FAISS index to save."
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
        if not os.path.exists(index_path):
            raise FileNotFoundError(
                f"FAISS index file not found at {index_path}"
            )

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(
                f"Metadata file not found at {metadata_path}"
            )

        self.index = faiss.read_index(index_path)

        self.documents = self.metadata_store.load(
            metadata_path,
        )
        
        

    def exists(
        self,
        index_path: str,
        metadata_path: str,
    ) -> bool:
        """
        Check whether a persisted index exists.
        """

        return (os.path.exists(index_path) and os.path.exists(metadata_path))