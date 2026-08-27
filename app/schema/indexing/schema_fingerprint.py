import hashlib
import json

from app.schema.models.schema_document import SchemaDocument


class SchemaFingerprint:
    """
    Creates deterministic fingerprints for schema documents.

    The fingerprint is used to determine whether a persisted
    FAISS index still represents the current database schema.

    If the database schema changes, the fingerprint changes
    and the semantic index can be rebuilt automatically.
    """

    @classmethod
    def create(
        cls,
        documents: list[SchemaDocument],
    ) -> str:
        """
        Generate a stable SHA-256 fingerprint for schema
        documents.

        Document order does not affect the fingerprint.
        """

        if not documents:
            return ""

        normalized_documents = []

        for document in sorted(
            documents,
            key=lambda item: item.id,
        ):

            normalized_documents.append(
                {
                    "id": document.id,
                    "table_name": document.table_name,
                    "content": document.content,
                    "metadata": cls._normalize_value(
                        document.metadata
                    ),
                }
            )

        serialized = json.dumps(
            normalized_documents,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    @classmethod
    def _normalize_value(
        cls,
        value,
    ):
        """
        Convert nested metadata into a deterministic,
        JSON-serializable representation.
        """

        if isinstance(value, dict):
            return {
                key: cls._normalize_value(
                    value[key]
                )
                for key in sorted(value)
            }

        if isinstance(value, list):
            normalized_items = [
                cls._normalize_value(item)
                for item in value
            ]

            # Lists containing dictionaries may contain
            # SQLAlchemy metadata whose ordering is not
            # semantically important. Sorting by canonical
            # JSON keeps fingerprint generation stable.
            try:
                return sorted(
                    normalized_items,
                    key=lambda item: json.dumps(
                        item,
                        sort_keys=True,
                        default=str,
                    ),
                )
            except TypeError:
                return normalized_items

        if isinstance(value, tuple):
            return [
                cls._normalize_value(item)
                for item in value
            ]

        if isinstance(value, set):
            return sorted(
                cls._normalize_value(item)
                for item in value
            )

        # SQLAlchemy metadata may occasionally contain
        # non-JSON-native values. Convert them safely.
        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)