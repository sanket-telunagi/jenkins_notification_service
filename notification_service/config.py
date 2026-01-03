# notification_service/config.py
import os
from dotenv import load_dotenv


class Settings:
    """
    Loads and holds all application settings from environment variables.
    """

    def __init__(self):
        load_dotenv()
        self.JENKINS_URL = os.getenv("JENKINS_URL")
        self.JENKINS_USER = os.getenv("JENKINS_USER")
        self.JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN")
        self.JENKINS_JOB_NAME = os.getenv("JENKINS_JOB_NAME", "global-email-sender")
        self.JENKINS_BUILD_TOKEN = os.getenv("JENKINS_BUILD_TOKEN")
        
        # Email recipient configuration
        self.EMAIL_TO_RECIPIENTS = self._parse_recipients(os.getenv("EMAIL_TO_RECIPIENTS", ""))
        self.EMAIL_CC_RECIPIENTS = self._parse_recipients(os.getenv("EMAIL_CC_RECIPIENTS", ""))
        self.EMAIL_BCC_RECIPIENTS = self._parse_recipients(os.getenv("EMAIL_BCC_RECIPIENTS", ""))
        
        # Workspace cleanup configuration (in minutes)
        self.WORKSPACE_CLEANUP_AGE_MINUTES = int(os.getenv("WORKSPACE_CLEANUP_AGE_MINUTES", "60"))

        self._validate()

    def _parse_recipients(self, recipients_str: str) -> list:
        """
        Parses a comma-separated string of email addresses into a list.
        
        Args:
            recipients_str: Comma-separated email addresses
            
        Returns:
            List of email addresses (empty list if string is empty)
        """
        if not recipients_str:
            return []
        return [email.strip() for email in recipients_str.split(",") if email.strip()]

    def _validate(self):
        """Ensures that all critical settings are present."""
        required_vars = [
            "JENKINS_URL",
            "JENKINS_USER",
            "JENKINS_API_TOKEN",
            "JENKINS_BUILD_TOKEN",
        ]
        missing = [var for var in required_vars if not getattr(self, var)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


# Create a singleton instance of the settings to be imported by other modules.
settings = Settings()
