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
    attachment_path: Optional[str] = None  # Keep for backward compatibility
    attachment_paths: List[str] = field(default_factory=list)  # NEW: Multiple attachments
    cc_recipients: List[str] = field(default_factory=list)
    bcc_recipients: List[str] = field(default_factory=list)

    def get_all_attachments(self) -> List[str]:
        """
        Get all attachments from both single and multiple attachment modes.
        
        Returns:
            List of attachment file paths (duplicates removed, order preserved)
        """
        attachments = []
        if self.attachment_path:
            attachments.append(self.attachment_path)
        if self.attachment_paths:
            attachments.extend(self.attachment_paths)
        # Remove duplicates while preserving order
        seen = set()
        return [x for x in attachments if not (x in seen or seen.add(x))]

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
