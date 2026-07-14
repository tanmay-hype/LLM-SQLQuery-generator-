import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.base import AppException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):

        logger.error(
            "Application exception on %s: %s",
            request.url.path,
            exc.message,
            exc_info=True,
        )

        response = {"error": exc.message}

        if exc.details is not None:
            response["details"] = exc.details

        return JSONResponse(
            status_code=exc.status_code,
            content=response,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception):

        logger.exception(
            "Unhandled exception on %s",
            request.url.path,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error"
            },
        )