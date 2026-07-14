from fastapi import FastAPI

from app.api.routes import router
from app.exceptions.handlers import register_exception_handlers


configure_logging()

app = FastAPI(
    title="LLM SQL Generator",
    version="1.0.0",
)

register_exception_handlers(app)


app.include_router(router)