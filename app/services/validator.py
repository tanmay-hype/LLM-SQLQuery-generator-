import re 
class SQLValidationError(Exception):
    """Raised when generated SQL is invalid."""
    pass

class SQLValidator:
    """
    Validates AI-generated SQL before execution.
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

    @classmethod
    def validate(cls, sql: str) -> str:
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
    