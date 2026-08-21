from app.schema.models.schema_document import SchemaDocument


class SchemaDocumentBuilder:
    """
    Converts raw database schema information into searchable
    SchemaDocument objects.

    Each table becomes one semantic schema document.

    The document contains:
        - table information
        - columns
        - primary keys
        - foreign keys
        - outgoing relationships
        - incoming/reverse relationships
        - related tables
        - semantic hints for common database concepts
    """

    # ======================================================
    # PUBLIC API
    # ======================================================

    def build(
        self,
        schema: dict,
    ) -> list[SchemaDocument]:
        """
        Build searchable semantic documents from the
        loaded database schema.
        """

        if not schema:
            return []

        # --------------------------------------------------
        # Build bidirectional relationship map.
        #
        # Example:
        #
        # orders.customer_id -> customers.id
        #
        # produces:
        #
        # orders    -> customers
        # customers -> orders
        #
        # This is useful for semantic retrieval because
        # either side of a relationship may be mentioned
        # in the user's question.
        # --------------------------------------------------

        related_table_map = (
            self._build_related_table_map(
                schema
            )
        )

        documents: list[SchemaDocument] = []

        for table_name, table_info in schema.items():

            columns = [
                column["name"]
                for column in table_info.get(
                    "columns",
                    [],
                )
                if column.get("name")
            ]

            primary_keys = (
                table_info
                .get(
                    "primary_keys",
                    {},
                )
                .get(
                    "constrained_columns",
                    [],
                )
            )

            foreign_keys = table_info.get(
                "foreign_keys",
                [],
            )

            related_tables = sorted(
                related_table_map.get(
                    table_name,
                    set(),
                )
            )

            content = self._build_content(
                table_name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys,
                related_tables=related_tables,
            )

            documents.append(
                SchemaDocument(
                    id=table_name,
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

    # ======================================================
    # RELATIONSHIP MAP
    # ======================================================

    @staticmethod
    def _build_related_table_map(
        schema: dict,
    ) -> dict[str, set[str]]:
        """
        Build a bidirectional map of related tables.

        Example:

            orders.customer_id -> customers.id

        produces:

            {
                "orders": {"customers"},
                "customers": {"orders"},
            }

        Foreign keys are directional at the database level,
        but semantic retrieval benefits from knowing the
        relationship from both sides.
        """

        related_table_map: dict[str, set[str]] = {
            table_name: set()
            for table_name in schema
        }

        for table_name, table_info in schema.items():

            foreign_keys = table_info.get(
                "foreign_keys",
                [],
            )

            for foreign_key in foreign_keys:

                referred_table = foreign_key.get(
                    "referred_table"
                )

                if not referred_table:
                    continue

                if referred_table not in schema:
                    continue

                # ------------------------------------------
                # Outgoing relationship
                #
                # orders -> customers
                # ------------------------------------------

                related_table_map[
                    table_name
                ].add(
                    referred_table
                )

                # ------------------------------------------
                # Reverse relationship
                #
                # customers -> orders
                # ------------------------------------------

                related_table_map[
                    referred_table
                ].add(
                    table_name
                )

        return related_table_map

    # ======================================================
    # SEMANTIC DOCUMENT CONSTRUCTION
    # ======================================================

    @staticmethod
    def _build_content(
        table_name: str,
        columns: list[str],
        primary_keys: list[str],
        foreign_keys: list[dict],
        related_tables: list[str],
    ) -> str:
        """
        Build the semantic text representation used by
        keyword and vector retrieval.
        """

        semantic_hints = (
            SchemaDocumentBuilder
            ._build_semantic_hints(
                table_name=table_name,
                columns=columns,
            )
        )

        relationships = (
            SchemaDocumentBuilder
            ._build_relationships(
                foreign_keys=foreign_keys,
            )
        )

        return f"""
Table: {table_name}

Purpose:
{SchemaDocumentBuilder._infer_table_purpose(table_name)}

Columns:
{SchemaDocumentBuilder._format_list(columns)}

Primary Keys:
{SchemaDocumentBuilder._format_list(primary_keys)}

Foreign Key Relationships:
{relationships}

Related Tables:
{SchemaDocumentBuilder._format_list(related_tables)}

Semantic Hints:
{semantic_hints}
""".strip()

    # ======================================================
    # TABLE PURPOSE
    # ======================================================

    @staticmethod
    def _infer_table_purpose(
        table_name: str,
    ) -> str:
        """
        Infer a basic semantic description from the
        table name.

        This is deterministic and does not call an LLM.

        These hints improve retrieval for common schemas,
        while unknown table names fall back to a generic
        description.
        """

        name = table_name.lower()

        if "customer" in name:
            return (
                "Stores customer or user information."
            )

        if (
            "order" in name
            and "item" not in name
        ):
            return (
                "Stores customer orders, purchases, "
                "and transaction information."
            )

        if (
            "order_item" in name
            or (
                "order" in name
                and "item" in name
            )
        ):
            return (
                "Stores individual products, items, "
                "or line items belonging to orders."
            )

        if "product" in name:
            return (
                "Stores product, inventory item, "
                "or catalog information."
            )

        if "payment" in name:
            return (
                "Stores payment, financial transaction, "
                "or settlement information."
            )

        if "invoice" in name:
            return (
                "Stores invoice, billing, or "
                "accounts-receivable information."
            )

        if "employee" in name:
            return (
                "Stores employee or staff information."
            )

        if "department" in name:
            return (
                "Stores department or organizational "
                "information."
            )

        if "user" in name:
            return (
                "Stores user or account information."
            )

        if "shipment" in name:
            return (
                "Stores shipping, delivery, or "
                "fulfillment information."
            )

        return (
            f"Stores data related to {table_name}."
        )

    # ======================================================
    # SEMANTIC COLUMN HINTS
    # ======================================================

    @staticmethod
    def _build_semantic_hints(
        table_name: str,
        columns: list[str],
    ) -> str:
        """
        Generate deterministic semantic descriptions
        for common column patterns.

        These descriptions are embedded with the schema
        document so natural-language phrases such as:

            "money spent"
            "revenue"
            "latest orders"
            "number of units"

        can match database columns even when the user does
        not use the exact physical column name.
        """

        hints: list[str] = []

        for column in columns:

            name = column.lower()

            # ----------------------------------------------
            # Total monetary amount
            # ----------------------------------------------

            if name == "total_amount":

                hints.append(
                    f"{column}: total monetary value, "
                    f"order value, spending, sales amount, "
                    f"or transaction amount associated "
                    f"with the record."
                )

            # ----------------------------------------------
            # Other financial columns
            #
            # This intentionally handles columns such as:
            #
            # unit_price
            # total_price
            # purchase_amount
            # item_cost
            # ----------------------------------------------

            elif any(
                keyword in name
                for keyword in {
                    "amount",
                    "price",
                    "cost",
                    "revenue",
                    "salary",
                    "value",
                }
            ):

                hints.append(
                    f"{column}: monetary or financial "
                    f"value associated with the record."
                )

            # ----------------------------------------------
            # Quantity / units
            # ----------------------------------------------

            elif any(
                keyword in name
                for keyword in {
                    "quantity",
                    "qty",
                    "units",
                }
            ):

                hints.append(
                    f"{column}: number of units, items, "
                    f"or records associated with the "
                    f"transaction."
                )

            # ----------------------------------------------
            # Foreign-key-like identifier
            # ----------------------------------------------

            elif name.endswith("_id"):

                entity_name = (
                    name[:-3]
                    .replace(
                        "_",
                        " ",
                    )
                )

                hints.append(
                    f"{column}: identifier referencing "
                    f"the related {entity_name} entity "
                    f"or record."
                )

            # ----------------------------------------------
            # Date columns
            # ----------------------------------------------

            elif name.endswith("_date"):

                hints.append(
                    f"{column}: date associated with "
                    f"the record and useful for time, "
                    f"trend, recent, monthly, daily, "
                    f"or historical analysis."
                )

            # ----------------------------------------------
            # Timestamp columns
            # ----------------------------------------------

            elif (
                name.endswith("_at")
                or "timestamp" in name
                or name.endswith("_time")
            ):

                hints.append(
                    f"{column}: timestamp associated "
                    f"with the record and useful for "
                    f"time-based or recency analysis."
                )

            # ----------------------------------------------
            # Human-readable labels
            # ----------------------------------------------

            elif name in {
                "name",
                "title",
                "label",
            }:

                hints.append(
                    f"{column}: human-readable name, "
                    f"title, or label for the record."
                )

            # ----------------------------------------------
            # Status/state columns
            # ----------------------------------------------

            elif name in {
                "status",
                "state",
            }:

                hints.append(
                    f"{column}: status or state of "
                    f"the record, useful for filtering."
                )

            # ----------------------------------------------
            # Category/type
            # ----------------------------------------------

            elif name in {
                "category",
                "type",
            }:

                hints.append(
                    f"{column}: category, classification, "
                    f"or type used to group records."
                )

            # ----------------------------------------------
            # Email
            # ----------------------------------------------

            elif "email" in name:

                hints.append(
                    f"{column}: email address associated "
                    f"with the record."
                )

            # ----------------------------------------------
            # Location
            # ----------------------------------------------

            elif name in {
                "city",
                "country",
                "state_code",
                "region",
            }:

                hints.append(
                    f"{column}: geographic or location "
                    f"information associated with "
                    f"the record."
                )

        if not hints:
            return (
                "No additional semantic hints."
            )

        return "\n".join(
            f"- {hint}"
            for hint in hints
        )

    # ======================================================
    # RELATIONSHIP FORMATTING
    # ======================================================

    @staticmethod
    def _build_relationships(
        foreign_keys: list[dict],
    ) -> str:
        """
        Convert SQLAlchemy foreign-key metadata into
        readable relationship descriptions.

        Example:

            customer_id -> customers.id
        """

        if not foreign_keys:
            return "None"

        relationships: list[str] = []

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

            local = ", ".join(
                constrained_columns
            )

            remote = ", ".join(
                referred_columns
            )

            if remote:

                relationships.append(
                    f"{local} → "
                    f"{referred_table}.{remote}"
                )

            else:

                relationships.append(
                    f"{local} → "
                    f"{referred_table}"
                )

        if not relationships:
            return "None"

        return "\n".join(
            f"- {relationship}"
            for relationship in relationships
        )

    # ======================================================
    # FORMATTING HELPERS
    # ======================================================

    @staticmethod
    def _format_list(
        values: list[str],
    ) -> str:
        """
        Format values as readable bullet points.
        """

        if not values:
            return "None"

        return "\n".join(
            f"- {value}"
            for value in values
        )