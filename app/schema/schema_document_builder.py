from app.schema.models.schema_document import SchemaDocument


class SchemaDocumentBuilder:
    """
    Converts raw schema into searchable documents.
    """

    def build(
        self,
        schema: dict,
    ) -> list[SchemaDocument]:

        documents = []

        for table_name, table in schema.items():

            columns = [
                column["name"]
                for column in table.get("columns", [])
            ]

            primary_keys = table.get(
                "primary_keys",
                {},
            ).get(
                "constrained_columns",
                [],
            )

            foreign_keys = [
                fk.get("referred_table")
                for fk in table.get(
                    "foreign_keys",
                    [],
                )
                if fk.get("referred_table")
            ]

            content = self._build_content(
                table_name,
                columns,
                primary_keys,
                foreign_keys,
            )

            documents.append(

                SchemaDocument(
                    table_name=table_name,
                    content=content,
                    metadata={
                        "columns": columns,
                        "primary_keys": primary_keys,
                        "foreign_keys": foreign_keys,
                    },
                )

            )

        return documents

    def _build_content(
        self,
        table_name: str,
        columns: list[str],
        primary_keys: list[str],
        foreign_keys: list[str],
    ) -> str:

        return f"""
Table: {table_name}

Columns:
{", ".join(columns)}

Primary Keys:
{", ".join(primary_keys) if primary_keys else "None"}

Related Tables:
{", ".join(foreign_keys) if foreign_keys else "None"}
""".strip()