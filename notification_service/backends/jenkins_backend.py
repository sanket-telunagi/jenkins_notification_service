# notification_service/backends/jenkins_backend.py
import os
import requests
from .base import BaseBackend
from ..config import Settings
from ..exceptions import BackendError
from ..models import EmailRequest


class JenkinsBackend(BaseBackend):
    """
    A notification backend that triggers a parameterized Jenkins job to send an email.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.build_url = f"{self.settings.JENKINS_URL}/job/{self.settings.JENKINS_JOB_NAME}/buildWithParameters"

    def send(self, email_request: EmailRequest) -> None:
        """
        Triggers the Jenkins email job with the provided email details.

        Args:
            email_request: The EmailRequest object.

        Raises:
            BackendError: If the request to Jenkins fails.
        """
        params = {
            "token": self.settings.JENKINS_BUILD_TOKEN,
            "RECIPIENTS": email_request.get_all_recipients_str(),
            "SUBJECT": email_request.subject,
            "BODY": email_request.body,
            "CONTENT_TYPE": email_request.content_type,
        }

        no_proxies = {
            "http": None,
            "https": None,
        }

        files = {}
        attachment_file = None

        try:
            if email_request.attachment_path:
                if not os.path.exists(email_request.attachment_path):
                    raise BackendError(
                        f"Attachment file not found at: {email_request.attachment_path}"
                    )

                # Open the file and prepare it for multipart upload
                attachment_file = open(email_request.attachment_path, "rb")
                files = {
                    "ATTACHMENT_FILE": (
                        os.path.basename(email_request.attachment_path),
                        attachment_file,
                    )
                }

            print(f"Triggering Jenkins job '{self.settings.JENKINS_JOB_NAME}'...")
            print(self.build_url)
            response = requests.post(
                self.build_url,
                auth=(self.settings.JENKINS_USER, self.settings.JENKINS_API_TOKEN),
                params=params,
                files=files,
                proxies=no_proxies,
            )
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

            print(f"Successfully triggered Jenkins job. Status: {response.status_code}")
            queue_url = response.headers.get("Location")
            if queue_url:
                print(f"Build is queued at: {queue_url.strip()}")

        except requests.exceptions.RequestException as e:
            raise BackendError(
                f"HTTP request to Jenkins failed: {e}", original_exception=e
            ) from e

        finally:
            # Ensure the file is closed if it was opened
            if attachment_file:
                attachment_file.close()
