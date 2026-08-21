from functools import lru_cache

from app.core.database import SessionLocal
from app.services.query_service import QueryService


@lru_cache(maxsize=1)
def get_query_service() -> QueryService:
    """
    Return the application-wide QueryService instance.

    QueryService owns reusable services such as:
        - schema loader
        - embedding service
        - FAISS vector store
        - schema index service
        - schema retrievers
        - intent detector
        - prompt builder
        - SQL generator
        - validators

    Reusing the service prevents the FAISS index from being
    reloaded from disk for every API request.
    """
    return QueryService()


def get_db():
    """
    Provide a database session for the duration
    of a request.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()