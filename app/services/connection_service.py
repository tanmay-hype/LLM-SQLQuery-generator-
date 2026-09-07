from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from app.models.connection import (
    DatabaseConnectionTestRequest,
    DatabaseConnectionTestResponse,
)


class DatabaseConnectionService:
    def test_connection(
        self,
        request: DatabaseConnectionTestRequest,
    ) -> DatabaseConnectionTestResponse:
        database_url = self._build_database_url(
            request
        )

        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 5,
            },
        )

        try:
            with engine.connect() as connection:
                connection.execute(
                    text("SELECT 1")
                )

                database = connection.execute(
                    text(
                        "SELECT current_database()"
                    )
                ).scalar_one()

                server_version = connection.execute(
                    text(
                        "SHOW server_version"
                    )
                ).scalar_one()

            return DatabaseConnectionTestResponse(
                success=True,
                message="Connection successful",
                database=database,
                server_version=str(
                    server_version
                ),
            )

        finally:
            engine.dispose()

    def _build_database_url(
        self,
        request: DatabaseConnectionTestRequest,
    ):
        if request.mode == "url":
            connection_url = (
                request.connection_url
                or ""
            ).strip()

            if not (
                connection_url.startswith(
                    "postgresql://"
                )
                or connection_url.startswith(
                    "postgresql+psycopg2://"
                )
            ):
                raise ValueError(
                    "Only PostgreSQL connection URLs "
                    "are supported"
                )

            return connection_url

        return URL.create(
            drivername="postgresql+psycopg2",
            username=request.username,
            password=request.password,
            host=request.host,
            port=request.port,
            database=request.database,
            query={
                "sslmode": request.ssl_mode,
            },
        )