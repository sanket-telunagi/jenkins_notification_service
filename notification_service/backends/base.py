# notification_service/backends/base.py
from abc import ABC, abstractmethod
from ..models import EmailRequest


class BaseBackend(ABC):
    """
    Abstract Base Class for all notification backends.
    It defines the interface that the NotificationClient will use.
    """

    @abstractmethod
    def send(self, email_request: EmailRequest) -> None:
        """
        Sends the email. This method must be implemented by all subclasses.

        Args:
            email_request: An EmailRequest object containing all email details.

        Raises:
            BackendError: If the email fails to send.
        """
        pass
