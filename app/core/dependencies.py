from app.core.database import SessionLocal
from app.services.query_service import QueryService


def get_query_service():
    return QueryService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
