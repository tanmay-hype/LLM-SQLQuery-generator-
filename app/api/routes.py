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
    return query_service.generate_sql(request.question)

@router.get("/")
def health():
    return {
        "status": "ok"
    }