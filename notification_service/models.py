# notification_service/models.py
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EmailRequest:
    """
    Represents a request to send an email.
    Provides a structured way to pass email data through the system.
    """

    to_recipients: List[str]
    subject: str
    body: str
    content_type: str = "text/html"
    attachment_path: Optional[str] = None
    cc_recipients: List[str] = field(default_factory=list)
    bcc_recipients: List[str] = field(default_factory=list)

    def get_all_recipients_str(self) -> str:
        """
        Returns a comma-separated string of all recipients for Jenkins,
        handling To, CC, and BCC.
        """
        all_recipients = set(self.to_recipients)

        # Jenkins Email Extension Plugin format for CC and BCC
        if self.cc_recipients:
            all_recipients.add(f"cc:{','.join(self.cc_recipients)}")
        if self.bcc_recipients:
            all_recipients.add(f"bcc:{','.join(self.bcc_recipients)}")

        return ",".join(all_recipients)
