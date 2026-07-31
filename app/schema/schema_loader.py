from sqlalchemy import inspect
from sqlalchemy.engine import Engine


class SchemaLoader:
    """
    Responsible for reading the database schema
    and converting it into a Python dictionary.
    """

    def __init__(self, engine: Engine):
        self.engine = engine
        self._inspector = None

    @property
    def inspector(self):
        """
        Lazily create the SQLAlchemy inspector.
        """
        if self._inspector is None:
            self._inspector = inspect(self.engine)
        return self._inspector

    def get_tables(self) -> list[str]:
        """
        Return all table names in the database.
        """
        return self.inspector.get_table_names()

    def get_columns(self, table: str) -> list[dict]:
        """
        Return all columns for a table.
        """
        return self.inspector.get_columns(table)

    def get_primary_keys(self, table: str) -> dict:
        """
        Return the primary key definition for a table.
        """
        return self.inspector.get_pk_constraint(table)

    def get_foreign_keys(self, table: str) -> list[dict]:
        """
        Return the foreign key definitions for a table.
        """
        return self.inspector.get_foreign_keys(table)

    def load_schema(self) -> dict:
        """
        Read the complete database schema.

        Returns
        -------
        dict

        Example
        -------
        {
            "customers": {
                "columns": [...],
                "primary_keys": {...},
                "foreign_keys": [...]
            },
            "orders": {
                ...
            }
        }
        """

        schema = {}

        for table in self.get_tables():

            schema[table] = {
                "columns": self.get_columns(table),
                "primary_keys": self.get_primary_keys(table),
                "foreign_keys": self.get_foreign_keys(table),
            }

        return schema