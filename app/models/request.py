from pydantic import BaseModel, Field


class SQLRequest(BaseModel):
    """
    Request model for SQL generation.
    """

    question: str = Field(
        ...,
        min_length=1,
        description="Natural language question.",
    )

    connection_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Active database connection ID."
        ),
    )