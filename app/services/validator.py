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
    """Validates AI-generated SQL before execution."""

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

    @classmethod
    def validate(cls, sql: str, schema: dict) -> str:
        """
        Validate SQL.

        Returns the cleaned SQL if valid.

        Raises:
            SQLValidationError
        """

        sql = sql.strip()

        if not sql:
            raise SQLValidationError("Generated SQL is empty.")

        cls._validate_single_statement(sql)
        cls._validate_select_only(sql)
        cls._validate_forbidden_keywords(sql)
        cls._validate_comments(sql)
        cls._validate_against_schema(sql, schema)

        return sql

    @staticmethod
    def _validate_single_statement(sql: str):
        statements = [s.strip() for s in sql.split(";") if s.strip()]

        if len(statements) > 1:
            raise SQLValidationError(
                "Multiple SQL statements are not allowed."
            )

    @staticmethod
    def _validate_select_only(sql: str):
        if not re.match(r"^\s*SELECT\b", sql, re.IGNORECASE):
            raise SQLValidationError(
                "Only SELECT statements are allowed."
            )

    @classmethod
    def _validate_forbidden_keywords(cls, sql: str):
        upper_sql = sql.upper()

        for keyword in cls.FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{keyword}\b", upper_sql):
                raise SQLValidationError(
                    f"Forbidden keyword detected: {keyword}"
                )

    @staticmethod
    def _validate_comments(sql: str):
        if "--" in sql:
            raise SQLValidationError(
                "SQL comments are not allowed."
            )

        if "/*" in sql or "*/" in sql:
            raise SQLValidationError(
                "SQL comments are not allowed."
            )

    @classmethod
    def _validate_against_schema(cls, sql: str, schema: dict):
        if parse_one is None or exp is None:
            raise SQLValidationError(
                "sqlglot is required for schema-aware validation. Install dependencies in your active environment."
            )

        try:
            statement = parse_one(sql, read="postgres")
        except ParseError as exc:
            raise SQLValidationError(f"Invalid SQL syntax: {exc}") from exc

        schema_table_names = set(schema.keys())
        if not schema_table_names:
            raise SQLValidationError("Schema is empty; cannot validate SQL.")

        cte_names = {
            cte.alias_or_name
            for cte in statement.find_all(exp.CTE)
            if cte.alias_or_name
        }

        table_alias_to_name = {}
        referenced_tables = set()

        for table in statement.find_all(exp.Table):
            table_name = table.name
            if not table_name or table_name in cte_names:
                continue

            referenced_tables.add(table_name)
            if table.alias_or_name:
                table_alias_to_name[table.alias_or_name] = table_name

        unknown_tables = sorted(referenced_tables - schema_table_names)
        if unknown_tables:
            raise SQLValidationError(
                "Unknown table(s) referenced: " + ", ".join(unknown_tables)
            )

        schema_columns_by_table = {
            table_name: {
                column["name"] for column in table_info.get("columns", [])
            }
            for table_name, table_info in schema.items()
        }

        referenced_schema_tables = {
            table_name for table_name in referenced_tables if table_name in schema
        }
        available_columns = set()
        for table_name in referenced_schema_tables:
            available_columns.update(schema_columns_by_table.get(table_name, set()))

        for column in statement.find_all(exp.Column):
            column_name = column.name
            if not column_name or column_name == "*":
                continue

            qualifier = column.table
            if qualifier:
                table_name = table_alias_to_name.get(qualifier, qualifier)
                if table_name not in schema_columns_by_table:
                    raise SQLValidationError(
                        f"Unknown table alias or table in column reference: {qualifier}.{column_name}"
                    )

                if column_name not in schema_columns_by_table[table_name]:
                    raise SQLValidationError(
                        f"Unknown column referenced: {table_name}.{column_name}"
                    )
            else:
                if column_name not in available_columns:
                    raise SQLValidationError(
                        f"Unknown column referenced: {column_name}"
                    )
    