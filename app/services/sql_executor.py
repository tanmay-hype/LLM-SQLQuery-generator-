from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.exceptions import SQLExecutionError


from app.core.database import engine


class SQLExecutor:
    """
    Executes validated SQL against PostgreSQL.
    """

    @staticmethod
    def execute(sql: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.

        Args:
            sql: Validated SQL query.

        Returns:
            List of dictionaries.
        """

        try:

            with engine.connect() as connection:

                result = connection.execute(text(sql))

                rows = result.mappings().all()

                return [dict(row) for row in rows]

        except SQLAlchemyError as e:
            raise SQLExecutionError(str(e))