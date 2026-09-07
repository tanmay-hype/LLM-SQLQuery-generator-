from fastapi import (
    APIRouter,
    HTTPException,
)
from sqlalchemy.exc import (
    OperationalError,
    SQLAlchemyError,
)

from app.models.connection import (
    DatabaseConnectionCreateResponse,
    DatabaseConnectionTestRequest,
    DatabaseConnectionTestResponse,
)
from app.services.connection_manager import (
    DatabaseConnectionManager,
)
from app.services.connection_service import (
    DatabaseConnectionService,
)


router = APIRouter(
    prefix="/connections",
    tags=["connections"],
)

connection_service = (
    DatabaseConnectionService()
)

connection_manager = (
    DatabaseConnectionManager()
)


@router.post(
    "/test",
    response_model=DatabaseConnectionTestResponse,
)
def test_database_connection(
    request: DatabaseConnectionTestRequest,
):
    try:
        return (
            connection_service
            .test_connection(request)
        )

    except OperationalError:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not connect to PostgreSQL. "
                "Check the host, port, database, "
                "username, password, and SSL settings."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=400,
            detail=(
                "PostgreSQL connection failed."
            ),
        )


@router.post(
    "",
    response_model=DatabaseConnectionCreateResponse,
    status_code=201,
)
def create_database_connection(
    request: DatabaseConnectionTestRequest,
):
    try:
        connection = (
            connection_manager
            .create_connection(request)
        )

        return (
            DatabaseConnectionCreateResponse(
                connection_id=(
                    connection.connection_id
                ),
                database=(
                    connection.database
                ),
                server_version=(
                    connection.server_version
                ),
            )
        )

    except OperationalError:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not connect to PostgreSQL."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=400,
            detail=(
                "PostgreSQL connection failed."
            ),
        )