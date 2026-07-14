from app.exceptions.base import AppException


class PromptBuildError(AppException):
    """
    Raised when prompt creation fails.
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


class LLMGenerationError(AppException):
    """
    Raised when the LLM cannot generate SQL.
    """

    def __init__(
        self,
        message: str,
        details=None,
    ):
        super().__init__(
            message=message,
            status_code=502,
            details=details,
        )