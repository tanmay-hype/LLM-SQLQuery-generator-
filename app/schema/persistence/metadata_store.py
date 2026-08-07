import json
from pathlib import Path

from app.schema.models.schema_document import SchemaDocument


class MetadataStore:
    """
    Persists SchemaDocument metadata alongside the FAISS index.
    """

    def save(
        self,
        path: str,
        documents: list[SchemaDocument],
    ) -> None:

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

        Path(path).write_text(
            json.dumps(payload, indent=4),
            encoding="utf-8",
        )

    def load(
        self,
        path: str,
    ) -> list[SchemaDocument]:

        raw = json.loads(
            Path(path).read_text(
                encoding="utf-8"
            )
        )

        documents = []

        for item in raw:

            documents.append(
                SchemaDocument(
                    id=item["id"],
                    table_name=item["table_name"],
                    content=item["content"],
                    metadata=item.get("metadata", {}),
                )
            )

        return documents

    def exists(
        self,
        path: str,
    ) -> bool:

        return Path(path).exists()