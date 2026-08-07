import json
from pathlib import Path

from app.schema.models.schema_document import SchemaDocument


class MetadataStore:
    """
    Persists schema documents alongside the FAISS index.
    """

    def save(
        self,
        path: str,
        documents: list[SchemaDocument],
    ) -> None:

        data = []

        for document in documents:

            data.append(
                {
                    "id": document.id,
                    "content": document.content,
                    "table": document.table,
                }
            )

        Path(path).write_text(
            json.dumps(data, indent=4),
            encoding="utf-8",
        )

    def load(
        self,
        path: str,
    ) -> list[SchemaDocument]:

        raw = json.loads(
            Path(path).read_text(
                encoding="utf-8",
            )
        )

        documents = []

        for item in raw:

            documents.append(
                SchemaDocument(
                    id=item["id"],
                    content=item["content"],
                    table=item["table"],
                )
            )

        return documents

    def exists(
        self,
        path: str,
    ) -> bool:

        return Path(path).exists()