class MonitorNotFound(Exception):
    """Raised when a monitor is not found"""


class InvalidRetryCount(ValueError):
    """Raised when a retry count is invalid"""


class InvalidMonitorUpdate(ValueError):
    """Raised when an update touches fields that can't be changed"""
