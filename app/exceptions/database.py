from app.exceptions.base import AppException


class SQLExecutionError(AppException):
    """
    Raised when SQL execution fails.
    """

    def __init__(
        self,
        message: str,
        details=None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            details=details,
        )


class SchemaLoadError(AppException):
    """
    Raised when database schema cannot be loaded.
    """

    def __init__(
        self,
        message: str,
        details=None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            details=details,
        )