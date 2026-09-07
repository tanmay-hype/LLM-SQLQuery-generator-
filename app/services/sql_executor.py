from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions import SQLExecutionError


class SQLExecutor:
    """
    Executes validated SQL against PostgreSQL.
    """

    def __init__(self, engine: Engine):
        self.engine = engine

    def execute(
        self,
        sql: str,
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query and return results.
        """

        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    text(sql)
                )

                rows = result.mappings().all()

                return [
                    dict(row)
                    for row in rows
                ]

        except SQLAlchemyError as exc:
            raise SQLExecutionError(
                str(exc)
            ) from exc