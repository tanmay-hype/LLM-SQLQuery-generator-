import re

from app.exceptions import SQLValidationError


try:
    from sqlglot import exp, parse_one
    from sqlglot.errors import ParseError
except ImportError:  # pragma: no cover - depends on runtime environment
    exp = None
    parse_one = None
    ParseError = Exception


class SQLValidator:
    """
    Validates AI-generated SQL before execution.

    Responsibilities
    ----------------
    1. Ensure SQL is not empty.
    2. Allow only a single SELECT statement.
    3. Reject dangerous SQL keywords.
    4. Reject SQL comments.
    5. Validate SQL syntax using sqlglot.
    6. Validate referenced tables against the database schema.
    7. Validate referenced columns against the database schema.
    8. Allow SQL aliases such as:

           SELECT DATE_TRUNC('month', order_date) AS month
           GROUP BY month
           ORDER BY month

    9. Support table aliases and CTEs.
    """

    FORBIDDEN_KEYWORDS = {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
    }

    # ======================================================
    # PUBLIC API
    # ======================================================

    @classmethod
    def validate(
        cls,
        sql: str,
        schema: dict,
    ) -> str:
        """
        Validate SQL.

        Returns
        -------
        str
            Cleaned SQL if validation succeeds.

        Raises
        ------
        SQLValidationError
            If the SQL is invalid or unsafe.
        """

        sql = sql.strip()

        if not sql:
            raise SQLValidationError(
                "Generated SQL is empty."
            )

        cls._validate_single_statement(sql)
        cls._validate_select_only(sql)
        cls._validate_forbidden_keywords(sql)
        cls._validate_comments(sql)
        cls._validate_against_schema(
            sql=sql,
            schema=schema,
        )

        return sql

    # ======================================================
    # BASIC VALIDATION
    # ======================================================

    @staticmethod
    def _validate_single_statement(
        sql: str,
    ) -> None:
        """
        Ensure that only one SQL statement is present.
        """

        statements = [
            statement.strip()
            for statement in sql.split(";")
            if statement.strip()
        ]

        if len(statements) > 1:
            raise SQLValidationError(
                "Multiple SQL statements are not allowed."
            )

    # ------------------------------------------------------

    @staticmethod
    def _validate_select_only(
        sql: str,
    ) -> None:
        """
        Only SELECT statements are allowed.
        """

        if not re.match(
            r"^\s*SELECT\b",
            sql,
            re.IGNORECASE,
        ):
            raise SQLValidationError(
                "Only SELECT statements are allowed."
            )

    # ------------------------------------------------------

    @classmethod
    def _validate_forbidden_keywords(
        cls,
        sql: str,
    ) -> None:
        """
        Reject dangerous SQL operations.
        """

        upper_sql = sql.upper()

        for keyword in cls.FORBIDDEN_KEYWORDS:

            if re.search(
                rf"\b{keyword}\b",
                upper_sql,
            ):
                raise SQLValidationError(
                    f"Forbidden keyword detected: {keyword}"
                )

    # ------------------------------------------------------

    @staticmethod
    def _validate_comments(
        sql: str,
    ) -> None:
        """
        Reject SQL comments.
        """

        if "--" in sql:
            raise SQLValidationError(
                "SQL comments are not allowed."
            )

        if "/*" in sql or "*/" in sql:
            raise SQLValidationError(
                "SQL comments are not allowed."
            )

    # ======================================================
    # SCHEMA VALIDATION
    # ======================================================

    @classmethod
    def _validate_against_schema(
        cls,
        sql: str,
        schema: dict,
    ) -> None:
        """
        Validate tables, columns, aliases and CTEs
        against the supplied database schema.
        """

        if parse_one is None or exp is None:
            raise SQLValidationError(
                "sqlglot is required for schema-aware validation. "
                "Install dependencies in your active environment."
            )

        # --------------------------------------------------
        # Parse SQL
        # --------------------------------------------------

        try:
            statement = parse_one(
                sql,
                read="postgres",
            )

        except ParseError as exc:
            raise SQLValidationError(
                f"Invalid SQL syntax: {exc}"
            ) from exc

        # --------------------------------------------------
        # Validate schema
        # --------------------------------------------------

        schema_table_names = set(
            schema.keys()
        )

        if not schema_table_names:
            raise SQLValidationError(
                "Schema is empty; cannot validate SQL."
            )

        # ==================================================
        # CTE NAMES
        # ==================================================

        cte_names = {
            cte.alias_or_name
            for cte in statement.find_all(exp.CTE)
            if cte.alias_or_name
        }

        # ==================================================
        # TABLES AND TABLE ALIASES
        # ==================================================

        table_alias_to_name: dict[str, str] = {}
        referenced_tables: set[str] = set()

        for table in statement.find_all(exp.Table):

            table_name = table.name

            if not table_name:
                continue

            # A CTE is not a physical database table.
            if table_name in cte_names:
                continue

            referenced_tables.add(
                table_name
            )

            alias = table.alias_or_name

            if alias:
                table_alias_to_name[alias] = (
                    table_name
                )

        # --------------------------------------------------
        # Unknown tables
        # --------------------------------------------------

        unknown_tables = sorted(
            referenced_tables
            - schema_table_names
        )

        if unknown_tables:
            raise SQLValidationError(
                "Unknown table(s) referenced: "
                + ", ".join(unknown_tables)
            )

        # ==================================================
        # SCHEMA COLUMNS
        # ==================================================

        schema_columns_by_table = {
            table_name: {
                column.get("name")
                for column in table_info.get(
                    "columns",
                    [],
                )
                if column.get("name")
            }
            for table_name, table_info in schema.items()
        }

        # --------------------------------------------------
        # Columns available from referenced tables
        # --------------------------------------------------

        referenced_schema_tables = {
            table_name
            for table_name in referenced_tables
            if table_name in schema
        }

        available_columns: set[str] = set()

        for table_name in referenced_schema_tables:

            available_columns.update(
                schema_columns_by_table.get(
                    table_name,
                    set(),
                )
            )

        # ==================================================
        # SELECT ALIASES
        # ==================================================

        select_aliases = cls._extract_select_aliases(
            statement
        )

        # ==================================================
        # COLUMN VALIDATION
        # ==================================================

        for column in statement.find_all(
            exp.Column
        ):

            column_name = column.name

            if not column_name:
                continue

            # "*" is not a real column reference.
            if column_name == "*":
                continue

            qualifier = column.table

            # --------------------------------------------------
            # Qualified column
            #
            # Example:
            #
            # c.name
            # o.total_amount
            # customers.name
            # --------------------------------------------------

            if qualifier:

                table_name = (
                    table_alias_to_name.get(
                        qualifier,
                        qualifier,
                    )
                )

                if (
                    table_name
                    not in schema_columns_by_table
                ):
                    raise SQLValidationError(
                        "Unknown table alias or table "
                        f"in column reference: "
                        f"{qualifier}.{column_name}"
                    )

                if (
                    column_name
                    not in schema_columns_by_table[
                        table_name
                    ]
                ):
                    raise SQLValidationError(
                        "Unknown column referenced: "
                        f"{table_name}.{column_name}"
                    )

                continue

            # --------------------------------------------------
            # Unqualified column
            # --------------------------------------------------

            # SQL aliases are allowed in clauses such as:
            #
            # GROUP BY month
            # ORDER BY month
            #
            # where "month" may have been defined as:
            #
            # DATE_TRUNC(...) AS month
            #
            if column_name in select_aliases:
                continue

            # --------------------------------------------------
            # Physical database column
            # --------------------------------------------------

            if column_name not in available_columns:

                raise SQLValidationError(
                    "Unknown column referenced: "
                    f"{column_name}"
                )

    # ======================================================
    # SELECT ALIAS EXTRACTION
    # ======================================================

    @staticmethod
    def _extract_select_aliases(
        statement,
    ) -> set[str]:
        """
        Extract aliases defined in the SELECT clause.

        Example:

            SELECT
                DATE_TRUNC(
                    'month',
                    order_date
                ) AS month,
                COUNT(*) AS order_count

        returns:

            {
                "month",
                "order_count"
            }

        These aliases may subsequently be referenced
        by clauses such as ORDER BY and GROUP BY.
        """

        aliases: set[str] = set()

        # --------------------------------------------------
        # Find SELECT expressions
        # --------------------------------------------------

        select_expressions = []

        if isinstance(
            statement,
            exp.Select,
        ):
            select_expressions = (
                statement.expressions
            )
        else:
            select_node = statement.find(
                exp.Select
            )

            if select_node is not None:
                select_expressions = (
                    select_node.expressions
                )

        # --------------------------------------------------
        # Extract aliases
        # --------------------------------------------------

        for expression in select_expressions:

            alias = getattr(
                expression,
                "alias",
                None,
            )

            if alias:
                aliases.add(alias)

        return aliases