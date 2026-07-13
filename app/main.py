from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title = "LLM SQL Generator",
    version = "1.0.0"
    )

register_exception_handlers(app)
app.include_router(router)