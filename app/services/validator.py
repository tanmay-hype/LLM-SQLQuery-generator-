import re

from app.exceptions import SQLValidationError


try:
    from sqlglot import exp, parse_one
    from sqlglot.errors import ParseError
except ImportError:  # pragma: no cover
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
    8. Support table aliases.
    9. Support CTEs.
    10. Support SELECT aliases in GROUP BY / ORDER BY.

    Example supported query:

        SELECT
            DATE_TRUNC('month', order_date) AS month,
            COUNT(id) AS order_count
        FROM orders
        GROUP BY month
        ORDER BY month;
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
        Validate generated SQL.

        Returns
        -------
        str
            Validated SQL.

        Raises
        ------
        SQLValidationError
            If the SQL is invalid or unsafe.
        """

        if not isinstance(sql, str):
            raise SQLValidationError(
                "Generated SQL must be a string."
            )

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
        Ensure that SQL contains only one statement.
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

        CTE queries beginning with WITH are also valid,
        because they ultimately contain a SELECT.
        """

        if re.match(
            r"^\s*SELECT\b",
            sql,
            re.IGNORECASE,
        ):
            return

        if re.match(
            r"^\s*WITH\b",
            sql,
            re.IGNORECASE,
        ):
            return

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
        Validate SQL against the supplied database schema.
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

        if not schema:
            raise SQLValidationError(
                "Schema is empty; cannot validate SQL."
            )

        schema_table_names = set(
            schema.keys()
        )

        # ==================================================
        # CTE NAMES
        # ==================================================

        cte_names = {
            cte.alias_or_name
            for cte in statement.find_all(
                exp.CTE
            )
            if cte.alias_or_name
        }

        # ==================================================
        # TABLES AND TABLE ALIASES
        # ==================================================

        table_alias_to_name: dict[str, str] = {}

        referenced_tables: set[str] = set()

        for table in statement.find_all(
            exp.Table
        ):

            table_name = table.name

            if not table_name:
                continue

            # CTE references are not physical DB tables.
            if table_name in cte_names:
                continue

            referenced_tables.add(
                table_name
            )

            alias = table.alias

            if alias:
                table_alias_to_name[alias] = (
                    table_name
                )

        # --------------------------------------------------
        # Validate table names
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

        # ==================================================
        # AVAILABLE PHYSICAL COLUMNS
        # ==================================================

        referenced_schema_tables = {
            table_name
            for table_name in referenced_tables
            if table_name in schema_columns_by_table
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

        select_aliases = (
            cls._extract_select_aliases(
                statement
            )
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

            # --------------------------------------------------
            # Wildcard
            # --------------------------------------------------

            if column_name == "*":
                continue

            qualifier = column.table

            # ==================================================
            # QUALIFIED COLUMN
            # ==================================================

            if qualifier:

                table_name = (
                    table_alias_to_name.get(
                        qualifier,
                        qualifier,
                    )
                )

                # --------------------------------------------------
                # CTE column references
                # --------------------------------------------------

                if qualifier in cte_names:
                    continue

                # --------------------------------------------------
                # Unknown table / alias
                # --------------------------------------------------

                if (
                    table_name
                    not in schema_columns_by_table
                ):
                    raise SQLValidationError(
                        "Unknown table alias or table "
                        f"in column reference: "
                        f"{qualifier}.{column_name}"
                    )

                # --------------------------------------------------
                # Unknown physical column
                # --------------------------------------------------

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

            # ==================================================
            # UNQUALIFIED COLUMN
            # ==================================================

            # --------------------------------------------------
            # SELECT alias
            #
            # We allow SELECT aliases because PostgreSQL
            # allows them in GROUP BY and ORDER BY.
            #
            # Example:
            #
            # SELECT
            #     DATE_TRUNC('month', order_date) AS month
            # FROM orders
            # GROUP BY month
            # ORDER BY month
            # --------------------------------------------------

            if column_name in select_aliases:

                if cls._is_allowed_alias_reference(
                    column
                ):
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
        Extract aliases defined in SELECT expressions.

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
        """

        aliases: set[str] = set()

        # --------------------------------------------------
        # Locate SELECT node
        # --------------------------------------------------

        if isinstance(
            statement,
            exp.Select,
        ):
            select_node = statement

        else:
            select_node = statement.find(
                exp.Select
            )

        if select_node is None:
            return aliases

        # --------------------------------------------------
        # Extract aliases
        # --------------------------------------------------

        for expression in select_node.expressions:

            alias = getattr(
                expression,
                "alias",
                None,
            )

            if alias:
                aliases.add(
                    alias
                )

        return aliases

    # ======================================================
    # ALIAS REFERENCE VALIDATION
    # ======================================================

    @staticmethod
    def _is_allowed_alias_reference(
        column,
    ) -> bool:
        """
        Determine whether a SELECT alias is being used
        in a clause where it is valid to reference it.

        PostgreSQL commonly allows SELECT aliases in:

            ORDER BY
            GROUP BY

        but not generally in:

            WHERE
            HAVING
            JOIN ON

        This method walks up the sqlglot AST and determines
        the clause containing the column reference.
        """

        current = column

        while current is not None:

            # --------------------------------------------------
            # ORDER BY
            # --------------------------------------------------

            if isinstance(
                current,
                exp.Order,
            ):
                return True

            # --------------------------------------------------
            # GROUP BY
            # --------------------------------------------------

            if isinstance(
                current,
                exp.Group,
            ):
                return True

            # --------------------------------------------------
            # SELECT expression
            #
            # A SELECT alias definition itself should not be
            # treated as a reference to the alias.
            # --------------------------------------------------

            if isinstance(
                current,
                exp.Alias,
            ):
                return False

            current = getattr(
                current,
                "parent",
                None,
            )

        return False