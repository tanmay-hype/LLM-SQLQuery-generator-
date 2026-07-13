from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.services.validator import SQLValidationError
from app.services.sql_executor import SQLExecutionError 

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(SQLValidationError)
    async def sql_validation_handler(request: Request, exc: SQLValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": str(exc)},
        )

    @app.exception_handler(SQLExecutionError)
    async def sql_execution_handler(request: Request, exc: SQLExecutionError):
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)},
        )
    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error: " },
        )
        