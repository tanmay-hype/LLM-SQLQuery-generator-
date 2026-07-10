from app.core.database import SessionLocal, engine
from app.llm.prompt_builder import PromptBuilder
from app.llm.sql_generator import SQLGenerator
from app.schema.schema_formatter import SchemaFormatter
from app.schema.schema_loader import SchemaLoader
from app.services.query_service import QueryService
from app.services.sql_executor import SQLExecutor
from app.services.validator import SQLValidator


def get_query_service():
    return QueryService(
        schema_loader=SchemaLoader(engine),
        schema_formatter=SchemaFormatter(),
        prompt_builder=PromptBuilder(),
        sql_generator=SQLGenerator(),
        sql_validator=SQLValidator(),
        sql_executor=SQLExecutor(),
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
