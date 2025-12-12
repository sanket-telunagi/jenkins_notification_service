# notification_service/__init__.py

# Expose the primary client and data model for easy access.
# This allows users to do `from notification_service import NotificationClient`.
from .client import NotificationClient
from .models import EmailRequest
from .exceptions import NotificationError, BackendError

__all__ = ["NotificationClient", "EmailRequest", "NotificationError", "BackendError"]
