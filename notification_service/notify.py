# notification_service/notify.py
"""
Simple notification function that uses configuration from .env for recipients.
"""
from typing import Optional
from .client import NotificationClient
from .models import EmailRequest
from .config import settings
from .exceptions import BackendError


def notify(
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
    content_type: str = "text/html"
) -> None:
    """
    Send an email notification using Jenkins backend.
    
    Recipients (TO, CC, BCC) are automatically loaded from .env file.
    
    Args:
        subject: Email subject line
        body: Email body content (HTML or plain text)
        attachment_path: Optional path to a file to attach
        content_type: Content type of the body (default: "text/html")
        
    Raises:
        BackendError: If the notification fails to send
        ValueError: If no TO recipients are configured in .env
        
    Example:
        >>> from jenkins_notification_service import notify
        >>> notify(
        ...     subject="Build Report",
        ...     body="<h1>Build Successful</h1>",
        ...     attachment_path="/path/to/report.txt"
        ... )
    """
    # Validate that we have at least TO recipients
    if not settings.EMAIL_TO_RECIPIENTS:
        raise ValueError(
            "No TO recipients configured. Please set EMAIL_TO_RECIPIENTS in .env file."
        )
    
    # Create email request with recipients from settings
    email_request = EmailRequest(
        to_recipients=settings.EMAIL_TO_RECIPIENTS,
        cc_recipients=settings.EMAIL_CC_RECIPIENTS,
        bcc_recipients=settings.EMAIL_BCC_RECIPIENTS,
        subject=subject,
        body=body,
        content_type=content_type,
        attachment_path=attachment_path
    )
    
    # Initialize client and send
    client = NotificationClient()
    client.send_email(email_request)

