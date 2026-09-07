from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DatabaseConnectionTestRequest(BaseModel):
    mode: Literal["url", "manual"]

    connection_url: str | None = None

    host: str | None = None
    port: int = Field(default=5432, ge=1, le=65535)
    database: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_mode: Literal[
        "disable",
        "prefer",
        "require",
    ] = "prefer"

    @model_validator(mode="after")
    def validate_connection_input(self):
        if self.mode == "url":
            if (
                self.connection_url is None
                or not self.connection_url.strip()
            ):
                raise ValueError(
                    "connection_url is required "
                    "when mode='url'"
                )

            return self

        required_fields = {
            "host": self.host,
            "database": self.database,
            "username": self.username,
            "password": self.password,
        }

        missing = [
            field_name
            for field_name, value in required_fields.items()
            if value is None or not value.strip()
        ]

        if missing:
            raise ValueError(
                "Missing required manual connection fields: "
                + ", ".join(missing)
            )

        return self


class DatabaseConnectionTestResponse(BaseModel):
    success: bool
    message: str
    database: str | None = None
    server_version: str | None = None