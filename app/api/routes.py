from fastapi import APIRouter

from app.core.config import settings
from app.core.dependencies import (
    get_connection_query_service,
    get_sql_cache,
)
from app.models.request import SQLRequest
from app.models.response import SQLResponse


router = APIRouter()


@router.post(
    "/generate-sql",
    response_model=SQLResponse,
    operation_id="generate_sql_hyphenated",
)
def generate_sql(
    request: SQLRequest,
):
    query_service = (
        get_connection_query_service(
            request.connection_id
        )
    )

    return query_service.generate_sql(
        request.question
    )


@router.get(
    "/cache/sql/stats",
    operation_id="get_sql_cache_stats",
)
def get_sql_cache_stats():
    cache = get_sql_cache()

    stats = cache.stats()

    return {
        "enabled": settings.sql_cache_enabled,
        **stats,
    }


@router.get("/")
def health():
    return {
        "status": "ok"
    }