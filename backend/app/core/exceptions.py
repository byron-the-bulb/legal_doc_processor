class AppException(Exception):
    """Base application exception"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ProcessingException(AppException):
    pass


class ValidationException(AppException):
    pass
