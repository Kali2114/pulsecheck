class MonitorNotFound(Exception):
    def __init__(self, monitor_id: int) -> None:
        self.monitor_id = monitor_id
        super().__init__(f"Monitor with id {monitor_id} not found")


class InvalidRetryCount(ValueError):
    """Raised when a retry count is invalid"""


class InvalidMonitorUpdate(ValueError):
    """Raised when an update touches fields that can't be changed"""


class EmailAlreadyRegistered(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email {email} already registered")


class UserNotFound(Exception):
    """Raised when a user is not found"""


class InvalidCredentials(Exception):
    """Raised when credentials are invalid"""


class PasswordTooLong(Exception):
    """Raised when a password is too long"""


class InvalidToken(Exception):
    """Raised when a token is invalid"""
