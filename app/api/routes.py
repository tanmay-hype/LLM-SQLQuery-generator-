from fastapi import APIRouter, Depends, HTTPException

from app.models.request import SQLRequest
from app.models.response import SQLResponse

from app.core.dependencies import get_query_service
from app.services.query_service import QueryService
from app.services.validator import SQLValidationError

from app.services.sql_executor import SQLExecutionError

router = APIRouter()

@router.post(
    "/generate-sql",
    response_model=SQLResponse,
    operation_id="generate_sql_hyphenated",
)
def generate_sql(
    request: SQLRequest,
    query_service: QueryService = Depends(get_query_service),
):
    """
    Convert natural language into SQL,
    execute it,
    and return the results.
    """

    try:
        return query_service.generate_sql(request.question)

    except SQLValidationError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except SQLExecutionError as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

"""  except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )"""
    

@router.get("/")
def health():
    return {
        "status": "ok"
    }