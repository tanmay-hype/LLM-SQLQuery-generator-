from fastapi import APIRouter, HTTPException

from app.core.database import engine
from app.models.request import SQLRequest
from app.models.response import SQLResponse

from app.schema.schema_loader import SchemaLoader
from app.schema.schema_formatter import SchemaFormatter
from app.llm.sql_generator import SQLGenerator
from app.llm.prompt_builder import PromptBuilder

from app.services.validator import SQLValidator, SQLValidationError

from app.services.sql_executor import SQLExecutor, SQLExecutionError

router = APIRouter()

@router.post(
    "/generate_sql",
    response_model=SQLResponse
)

def generate_sql(request: SQLRequest):
    """
    Convert natural language into SQL,
    execute it,
    and return the results.
    """

    try:
        loader = SchemaLoader(engine)

        # Load schema
        schema = loader.load_schema()

        # Format schema
        formatted_schema = SchemaFormatter.format(schema)

        # Build prompt
        prompt = PromptBuilder.build_prompt(
            schema=formatted_schema,
            user_question=request.question,
        )

        # Generate SQL
        generator = SQLGenerator()

        sql = generator.generate_sql(prompt)

        # Validate SQL
        SQLValidator.validate(sql)

        # Execute SQL
        results = SQLExecutor.execute(sql)

        return SQLResponse(
            sql=sql,
            results=results,
        )

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

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    

@router.get("/")
def health():
    return {
        "status": "ok"
    }