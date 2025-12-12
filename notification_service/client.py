# notification_service/client.py
from .config import settings
from .models import EmailRequest
from .backends.jenkins_backend import JenkinsBackend
from .backends.base import BaseBackend


class NotificationClient:
    """
    The public client for the notification service.
    It uses a configured backend to send notifications.
    """

    def __init__(self, backend: BaseBackend = None):
        """
        Initializes the client.
        If no backend is provided, it defaults to the JenkinsBackend.
        """
        if backend:
            self.backend = backend
        else:
            # The strategy is set here. Defaulting to Jenkins.
            self.backend = JenkinsBackend(settings)

    def send_email(self, email_request: EmailRequest) -> None:
        """
        Sends an email using the configured backend.

        Args:
            email_request: An EmailRequest object.
        """
        self.backend.send(email_request)
