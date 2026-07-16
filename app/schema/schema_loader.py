from sqlalchemy import inspect
from sqlalchemy.engine import Engine

class SchemaLoader:
    """
    Responsible for reading the database schema
    and converting it into a Python dictionary.
    """
    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = None

    def _get_inspector(self):
        if self.inspector is None:
            self.inspector = inspect(self.engine)
        return self.inspector

    def get_tables(self):
        """
        Returns a list of all table names in the database.
        """
        return self._get_inspector().get_table_names()

    def get_columns(self, table: str):
        """
        Returns a list of all columns in a given table.
        """
        return self._get_inspector().get_columns(table)

    def get_primary_keys(self, table: str):
        """
        Returns a list of primary key columns for a given table.
        """
        return self._get_inspector().get_pk_constraint(table)

    def get_foreign_keys(self, table: str):
        """
        Returns a list of foreign key constraints for a given table.
        """
        return self._get_inspector().get_foreign_keys(table)


    def load_schema(self):
        """
        Reads all tables and their columns.
        """
        schema = {}
        for table in self.get_tables():
            schema[table] = {
                    "columns": self.get_columns(table),
                    "primary_keys": self.get_primary_keys(table),
                    "foreign_keys": self.get_foreign_keys(table)
            }

        return schema
