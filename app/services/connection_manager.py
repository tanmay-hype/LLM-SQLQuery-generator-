from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.models.connection import (
    DatabaseConnectionTestRequest,
)
from app.services.connection_service import (
    DatabaseConnectionService,
)


@dataclass
class DatabaseConnection:
    connection_id: str
    engine: Engine
    database: str
    server_version: str


class DatabaseConnectionManager:
    def __init__(self):
        self._connections: dict[
            str,
            DatabaseConnection,
        ] = {}

        self._lock = Lock()

        self._connection_service = (
            DatabaseConnectionService()
        )

    def create_connection(
        self,
        request: DatabaseConnectionTestRequest,
    ) -> DatabaseConnection:
        test_result = (
            self._connection_service
            .test_connection(request)
        )

        database_url = (
            self._connection_service
            .build_database_url(request)
        )

        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 5,
            },
        )

        connection_id = str(uuid4())

        connection = DatabaseConnection(
            connection_id=connection_id,
            engine=engine,
            database=(
                test_result.database
                or ""
            ),
            server_version=(
                test_result.server_version
                or ""
            ),
        )

        with self._lock:
            self._connections[
                connection_id
            ] = connection

        return connection

    def get_connection(
        self,
        connection_id: str,
    ) -> DatabaseConnection | None:
        with self._lock:
            return self._connections.get(
                connection_id
            )

    def remove_connection(
        self,
        connection_id: str,
    ) -> bool:
        with self._lock:
            connection = (
                self._connections.pop(
                    connection_id,
                    None,
                )
            )

        if connection is None:
            return False

        connection.engine.dispose()

        return True
    
connection_manager = DatabaseConnectionManager()