# notification_service/backends/jenkins_backend.py
import os
import shutil
import stat
import requests
import uuid
from datetime import datetime, timedelta
from pathlib import Path
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
        # Read Jenkins workspace path from environment
        self.jenkins_workspace = os.getenv("JENKINS_JOB_WORKSPACE")

    def _generate_unique_filename(self, original_path: str) -> str:
        """
        Generates a unique filename with timestamp and UUID.
        
        Format: basename_YYYYMMDD_HHMMSS_uuid4[:8].ext
        Example: report_20260103_143052_a1b2c3d4.txt
        
        Args:
            original_path: Original file path
            
        Returns:
            Unique filename string
        """
        path_obj = Path(original_path)
        basename = path_obj.stem  # filename without extension
        extension = path_obj.suffix  # .txt, .pdf, etc.
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate short UUID (first 8 characters)
        short_uuid = str(uuid.uuid4())[:8]
        
        # Combine: basename_timestamp_uuid.ext
        unique_filename = f"{basename}_{timestamp}_{short_uuid}{extension}"
        
        return unique_filename

    def _cleanup_old_files(self, workspace_dir: str, age_minutes: int = 60) -> None:
        """
        Cleans up old files from the workspace that match the unique filename pattern.
        
        Files older than age_minutes are deleted. This is a fallback cleanup for
        files that Jenkins failed to clean up.
        
        Args:
            workspace_dir: Path to Jenkins workspace directory
            age_minutes: Age threshold in minutes (default: 60)
        """
        if not workspace_dir or not os.path.exists(workspace_dir):
            return
        
        print(f"\n  Checking for old files (>{age_minutes} min) in workspace...")
        
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=age_minutes)
        cleanup_count = 0
        
        try:
            workspace_path = Path(workspace_dir)
            
            # Find files matching pattern: *_YYYYMMDD_HHMMSS_*.ext
            for file_path in workspace_path.glob("*_????????_??????_*.*"):
                try:
                    filename = file_path.name
                    
                    # Extract timestamp from filename (positions after first underscore)
                    # Format: basename_YYYYMMDD_HHMMSS_uuid.ext
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        date_part = parts[-3]  # YYYYMMDD
                        time_part = parts[-2]  # HHMMSS
                        
                        # Validate format
                        if len(date_part) == 8 and len(time_part) == 6:
                            timestamp_str = f"{date_part}_{time_part}"
                            file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                            
                            # Check if file is older than cutoff
                            if file_time < cutoff_time:
                                file_path.unlink()
                                cleanup_count += 1
                                age_minutes_actual = (current_time - file_time).total_seconds() / 60
                                print(f"    ✓ Cleaned up old file: {filename} (age: {age_minutes_actual:.1f} min)")
                
                except (ValueError, IndexError) as e:
                    # Skip files that don't match expected pattern
                    continue
                except Exception as e:
                    print(f"    ⚠ Warning: Could not clean up {file_path.name}: {e}")
                    continue
            
            if cleanup_count > 0:
                print(f"  ✓ Cleaned up {cleanup_count} old file(s)")
            else:
                print(f"  No old files to clean up")
                
        except Exception as e:
            print(f"  ⚠ Warning: Error during workspace cleanup: {e}")

    def _copy_to_workspace(self, source_path: str) -> tuple:
        """
        Copies the attachment file to Jenkins workspace with unique filename and 777 permissions.
        Also performs cleanup of old files before copying.

        Args:
            source_path: Path to the source file to copy.

        Returns:
            Tuple of (workspace_file_path, unique_filename)

        Raises:
            BackendError: If workspace path is not configured or copy fails.
        """
        print("\n" + "="*70)
        print("DEBUG: _copy_to_workspace() called")
        print("="*70)
        print(f"  Source file path: {source_path}")
        print(f"  Source file exists: {os.path.exists(source_path)}")
        if os.path.exists(source_path):
            print(f"  Source file size: {os.path.getsize(source_path)} bytes")
            print(f"  Source file permissions: {oct(os.stat(source_path).st_mode)[-3:]}")
        
        if not self.jenkins_workspace:
            raise BackendError("JENKINS_JOB_WORKSPACE environment variable is not set")

        print(f"  Jenkins workspace: {self.jenkins_workspace}")
        print(f"  Workspace exists: {os.path.exists(self.jenkins_workspace)}")

        if not os.path.exists(self.jenkins_workspace):
            raise BackendError(
                f"Jenkins workspace directory does not exist: {self.jenkins_workspace}"
            )

        # Clean up old files before copying new one
        cleanup_age = getattr(self.settings, 'WORKSPACE_CLEANUP_AGE_MINUTES', 60)
        self._cleanup_old_files(self.jenkins_workspace, cleanup_age)

        # Generate unique filename
        unique_filename = self._generate_unique_filename(source_path)
        workspace_file_path = os.path.join(self.jenkins_workspace, unique_filename)
        
        print(f"\n  Generated unique filename: {unique_filename}")
        print(f"  Destination full path: {workspace_file_path}")

        try:
            # Copy the file to workspace
            print(f"  Copying file...")
            shutil.copy(source_path, workspace_file_path)
            print(f"  ✓ File copied successfully")
            
            # Set 777 permissions (rwxrwxrwx)
            print(f"  Setting permissions to 777...")
            os.chmod(workspace_file_path, 0o777)
            
            # Verify the copy
            if os.path.exists(workspace_file_path):
                print(f"  ✓ Destination file exists")
                print(f"  Destination file size: {os.path.getsize(workspace_file_path)} bytes")
                print(f"  Destination file permissions: {oct(os.stat(workspace_file_path).st_mode)[-3:]}")
            else:
                print(f"  ✗ WARNING: Destination file does not exist!")
            
            print("="*70)
            return workspace_file_path, unique_filename
        except Exception as e:
            print(f"  ✗ ERROR during copy: {e}")
            print("="*70)
            raise BackendError(
                f"Failed to copy file to Jenkins workspace: {e}", original_exception=e
            ) from e

    def _cleanup_workspace_file(self, workspace_path: str) -> None:
        """
        Removes a file from the Jenkins workspace.

        Args:
            workspace_path: Path to the file in Jenkins workspace to remove.
        """
        print("\n" + "="*70)
        print("DEBUG: _cleanup_workspace_file() called")
        print("="*70)
        print(f"  Workspace path: {workspace_path}")
        
        if not workspace_path:
            print(f"  No workspace path provided, skipping cleanup")
            print("="*70 + "\n")
            return
            
        print(f"  File exists before cleanup: {os.path.exists(workspace_path)}")
        
        if not os.path.exists(workspace_path):
            print(f"  File does not exist, skipping cleanup")
            print("="*70 + "\n")
            return

        try:
            os.remove(workspace_path)
            print(f"  ✓ Successfully removed workspace file")
            print(f"  File exists after cleanup: {os.path.exists(workspace_path)}")
            print("="*70 + "\n")
        except Exception as e:
            # Log the error but don't raise - cleanup failures shouldn't mask original errors
            print(f"  ✗ WARNING: Failed to clean up workspace file: {e}")
            print("="*70 + "\n")

    def send(self, email_request: EmailRequest) -> None:
        """
        Triggers the Jenkins email job with the provided email details.

        Args:
            email_request: The EmailRequest object.

        Raises:
            BackendError: If the request to Jenkins fails.
        """
        workspace_file_path = None
        unique_filename = None

        try:
            print("\n" + "="*70)
            print("DEBUG: JenkinsBackend.send() called")
            print("="*70)
            
            # Prepare base parameters
            params = {
                "token": self.settings.JENKINS_BUILD_TOKEN,
                "RECIPIENTS": email_request.get_all_recipients_str(),
                "SUBJECT": email_request.subject,
                "BODY": email_request.body,
                "CONTENT_TYPE": email_request.content_type,
                "WORKSPACE_CLEANUP_AGE_MINUTES": str(getattr(self.settings, 'WORKSPACE_CLEANUP_AGE_MINUTES', 60))
            }
            
            print(f"Email parameters:")
            print(f"  Recipients: {params['RECIPIENTS']}")
            print(f"  Subject: {params['SUBJECT']}")
            print(f"  Content type: {params['CONTENT_TYPE']}")
            print(f"  Attachment path from request: {email_request.attachment_path}")
            print(f"  Attachment paths from request: {email_request.attachment_paths}")

            # Handle attachments if provided
            all_attachments = email_request.get_all_attachments()
            
            if all_attachments:
                print(f"\n  Processing {len(all_attachments)} attachment(s)...")
                
                workspace_filenames = []
                workspace_file_paths = []
                
                for i, attachment_path in enumerate(all_attachments, 1):
                    if not os.path.exists(attachment_path):
                        raise BackendError(
                            f"Attachment file not found at: {attachment_path}"
                        )
                    
                    # Copy each attachment to Jenkins workspace (returns tuple)
                    ws_path, unique_name = self._copy_to_workspace(attachment_path)
                    workspace_file_paths.append(ws_path)
                    workspace_filenames.append(unique_name)
                    
                    file_size = os.path.getsize(attachment_path)
                    print(f"    [{i}/{len(all_attachments)}] ✓ {Path(attachment_path).name} "
                          f"({file_size / 1024:.1f} KB) → {unique_name}")
                
                # Jenkins Email Extension supports comma-separated attachment paths
                params["ATTACHMENT_PATH"] = ",".join(workspace_filenames)
                params["CLEANUP_FILE"] = ",".join(workspace_filenames)
                
                print(f"\n  ✓ All {len(workspace_filenames)} attachment(s) processed")
                total_size = sum(os.path.getsize(Path(p)) for p in all_attachments)
                print(f"    Total size: {total_size / 1024:.1f} KB")
                print(f"    Workspace files: {', '.join(workspace_filenames[:2])}")
                if len(workspace_filenames) > 2:
                    print(f"    ... and {len(workspace_filenames) - 2} more")
            else:
                print(f"  No attachments provided in email request")

            no_proxies = {
                "http": None,
                "https": None,
            }

            print(f"\n" + "-"*70)
            print(f"Triggering Jenkins job: '{self.settings.JENKINS_JOB_NAME}'")
            print(f"Jenkins URL: {self.build_url}")
            print(f"\nALL PARAMETERS being sent to Jenkins:")
            print("-"*70)
            for key, value in params.items():
                if key == "BODY":
                    print(f"  {key}: <HTML content, {len(value)} characters>")
                elif key == "token":
                    print(f"  {key}: <hidden>")
                else:
                    print(f"  {key}: {value}")
            print("-"*70)
            print(f"Total parameters: {len(params)}")
            if "ATTACHMENT_PATH" in params:
                print(f"✓ ATTACHMENT_PATH parameter included: '{params['ATTACHMENT_PATH']}'")
            if "CLEANUP_FILE" in params:
                print(f"✓ CLEANUP_FILE parameter included: '{params['CLEANUP_FILE']}'")
                print(f"  This file will be available in workspace for Jenkins to use")
            print("-"*70)
            
            # Separate token (must be in URL) from other parameters (sent in body)
            # This prevents "414 URI Too Long" errors with large HTML bodies
            token = params.pop("token")
            url_params = {"token": token}
            
            # Send large parameters (BODY, etc.) in request body to avoid URL length limits
            response = requests.post(
                self.build_url,
                auth=(self.settings.JENKINS_USER, self.settings.JENKINS_API_TOKEN),
                params=url_params,  # Only token in URL
                data=params,        # Everything else in request body
                proxies=no_proxies,
            )
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

            print(f"\n✓ Successfully triggered Jenkins job!")
            print(f"  Response status: {response.status_code}")
            queue_url = response.headers.get("Location")
            if queue_url:
                print(f"  Build queued at: {queue_url.strip()}")
            
            if unique_filename:
                print(f"\n  NOTE: File '{unique_filename}' remains in workspace")
                print(f"        Jenkins job will clean it up after sending email")
                print(f"        Fallback cleanup: Files older than {getattr(self.settings, 'WORKSPACE_CLEANUP_AGE_MINUTES', 60)} minutes")
            
            print("="*70 + "\n")

        except requests.exceptions.RequestException as e:
            print(f"\n✗ HTTP request to Jenkins failed: {e}")
            print("="*70 + "\n")
            raise BackendError(
                f"HTTP request to Jenkins failed: {e}", original_exception=e
            ) from e

        finally:
            # No immediate cleanup - Jenkins will handle it
            # Fallback cleanup happens on next run for files > age threshold
            pass
