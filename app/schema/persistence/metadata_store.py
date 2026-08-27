import json
from pathlib import Path

from app.schema.indexing.schema_fingerprint import (
    SchemaFingerprint,
)
from app.schema.models.schema_document import (
    SchemaDocument,
)


class MetadataStore:
    """
    Persists SchemaDocument metadata alongside the FAISS index.

    The persisted schema documents are also used to determine
    whether the FAISS index still matches the current database
    schema.
    """

    # ======================================================
    # SAVE
    # ======================================================

    def save(
        self,
        path: str,
        documents: list[SchemaDocument],
    ) -> None:
        """
        Persist schema documents as JSON metadata.
        """

        payload = []

        for document in documents:

            payload.append(
                {
                    "id": document.id,
                    "table_name": document.table_name,
                    "content": document.content,
                    "metadata": document.metadata,
                }
            )

        metadata_path = Path(path)

        metadata_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        metadata_path.write_text(
            json.dumps(
                payload,
                indent=4,
                default=str,
            ),
            encoding="utf-8",
        )

    # ======================================================
    # LOAD
    # ======================================================

    def load(
        self,
        path: str,
    ) -> list[SchemaDocument]:
        """
        Load persisted schema documents.
        """

        metadata_path = Path(path)

        raw = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        documents: list[
            SchemaDocument
        ] = []

        for item in raw:

            documents.append(
                SchemaDocument(
                    id=item["id"],
                    table_name=item["table_name"],
                    content=item["content"],
                    metadata=item.get(
                        "metadata",
                        {},
                    ),
                )
            )

        return documents

    # ======================================================
    # FINGERPRINT
    # ======================================================

    def fingerprint(
        self,
        path: str,
    ) -> str:
        """
        Calculate the fingerprint of the persisted schema
        documents.

        This allows SchemaIndexService to determine whether
        an existing FAISS index is stale.
        """

        if not self.exists(path):
            return ""

        documents = self.load(
            path
        )

        return SchemaFingerprint.create(
            documents
        )

    # ======================================================
    # EXISTS
    # ======================================================

    @staticmethod
    def exists(
        path: str,
    ) -> bool:
        """
        Return True when the metadata file exists.
        """

        return Path(path).exists()