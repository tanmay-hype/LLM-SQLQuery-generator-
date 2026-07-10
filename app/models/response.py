from typing import Any 
from pydantic import BaseModel

class SQLResponse(BaseModel):
    """
    Response model for SQL execution results.
    """

    sql: str
    results: list[dict[str, Any]]