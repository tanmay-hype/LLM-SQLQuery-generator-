from app.exceptions.base import AppException


class SQLValidationError(AppException):
    """
    Raised when generated SQL fails validation.
    """

    def __init__(
        self,
        message: str,
        details=None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            details=details,
        )


class RequestValidationError(AppException):
    """
    Raised for business-level request validation.
    """

    def __init__(
        self,
        message: str,
        details=None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            details=details,
        )