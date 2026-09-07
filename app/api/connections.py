from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import (
    OperationalError,
    SQLAlchemyError,
)

from app.models.connection import (
    DatabaseConnectionTestRequest,
    DatabaseConnectionTestResponse,
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


@router.post(
    "/test",
    response_model=DatabaseConnectionTestResponse,
)
def test_database_connection(
    request: DatabaseConnectionTestRequest,
):
    try:
        return connection_service.test_connection(
            request
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