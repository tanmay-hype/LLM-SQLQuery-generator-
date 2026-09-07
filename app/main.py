from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.connections import router as connections_router
from app.api.routes import router
from app.core.logging import configure_logging
from app.exceptions.handlers import register_exception_handlers


configure_logging()

app = FastAPI(
    title="LLM SQL Generator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5183",
        "http://127.0.0.1:5182",

        
        
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(router)
app.include_router(connections_router)