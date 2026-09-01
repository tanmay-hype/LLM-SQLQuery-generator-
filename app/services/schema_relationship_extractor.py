from app.models.schema_relationship import (
    SchemaRelationship,
)


class SchemaRelationshipExtractor:
    """
    Extracts physical foreign-key relationships from the
    schema dictionary produced by SchemaLoader.
    """

    def extract(
        self,
        schema: dict,
    ) -> frozenset[SchemaRelationship]:
        """
        Convert SQLAlchemy foreign-key metadata into
        normalized SchemaRelationship objects.
        """

        relationships: set[
            SchemaRelationship
        ] = set()

        for table_name, table_info in schema.items():

            foreign_keys = table_info.get(
                "foreign_keys",
                [],
            )

            for foreign_key in foreign_keys:

                constrained_columns = (
                    foreign_key.get(
                        "constrained_columns",
                        [],
                    )
                )

                referred_table = (
                    foreign_key.get(
                        "referred_table"
                    )
                )

                referred_columns = (
                    foreign_key.get(
                        "referred_columns",
                        [],
                    )
                )

                if not referred_table:
                    continue

                if not constrained_columns:
                    continue

                if not referred_columns:
                    continue

                # ------------------------------------------
                # SQLAlchemy represents composite foreign
                # keys as corresponding column lists.
                #
                # zip() also handles the normal one-column
                # FK case used by the current database.
                # ------------------------------------------

                for (
                    source_column,
                    target_column,
                ) in zip(
                    constrained_columns,
                    referred_columns,
                ):

                    relationships.add(
                        SchemaRelationship(
                            source_table=table_name,
                            source_column=source_column,
                            target_table=referred_table,
                            target_column=target_column,
                        )
                    )

        return frozenset(
            relationships
        )