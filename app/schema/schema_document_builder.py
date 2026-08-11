
from app.schema.models.schema_document import SchemaDocument


class SchemaDocumentBuilder:
    """
    Converts raw database schema information into searchable
    SchemaDocument objects.

    Each table becomes one searchable document.
    """

    def build(
        self,
        schema: dict,
    ) -> list[SchemaDocument]:
        """
        Build searchable documents from the loaded schema.
        """

        documents: list[SchemaDocument] = []

        for table_name, table_info in schema.items():

            columns = [
                column["name"]
                for column in table_info.get("columns", [])
                if column.get("name")
            ]

            primary_keys = table_info.get(
                "primary_keys",
                {},
            ).get(
                "constrained_columns",
                [],
            )

            foreign_keys = table_info.get(
                "foreign_keys",
                [],
            )

            related_tables = [
                fk.get("referred_table")
                for fk in foreign_keys
                if fk.get("referred_table")
            ]

            content = self._build_content(
                table_name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                related_tables=related_tables,
            )

            documents.append(
                SchemaDocument(
                    table_name=table_name,
                    content=content,
                    metadata={
                        "columns": columns,
                        "primary_keys": primary_keys,
                        "foreign_keys": foreign_keys,
                        "related_tables": related_tables,
                    },
                )
            )

        return documents

    @staticmethod
    def _build_content(
        table_name: str,
        columns: list[str],
        primary_keys: list[str],
        related_tables: list[str],
    ) -> str:
        """
        Build the text representation used by
        keyword and semantic retrieval.
        """

        return f"""
Table: {table_name}

Columns:
{", ".join(columns) if columns else "None"}

Primary Keys:
{", ".join(primary_keys) if primary_keys else "None"}

Related Tables:
{", ".join(related_tables) if related_tables else "None"}
""".strip()

