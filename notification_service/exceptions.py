# notification_service/exceptions.py


class NotificationError(Exception):
    """Base exception for the notification service."""

    pass


class BackendError(NotificationError):
    """Raised when the notification backend fails to send the message."""

    def __init__(self, message: str, original_exception: Exception = None):
        self.original_exception = original_exception
        super().__init__(f"Notification backend failed: {message}")
