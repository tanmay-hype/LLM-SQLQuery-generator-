from pydantic import BaseModel, Field

class SQLRequest(BaseModel):
    """
    Request model for SQL generation.
    """

    question: str = Field(
        ...,  # Required field
        min_length=1,
        description="Natural language question."
    )