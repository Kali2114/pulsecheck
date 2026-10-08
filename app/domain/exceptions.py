class MonitorNotFound(Exception):
    """Raised when a monitor is not found"""


class InvalidRetryCount(ValueError):
    """Raised when a retry count is invalid"""


class InvalidMonitorUpdate(ValueError):
    """Raised when an update touches fields that can't be changed"""


class EmailAlreadyRegistered(Exception):
    """Raised when an email is already registered"""


class UserNotFound(Exception):
    """Raised when a user is not found"""


class InvalidCredentials(Exception):
    """Raised when credentials are invalid"""
