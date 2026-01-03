<div align="center">
  <img src="assets/jenkins_boy.png" alt="Notification Service Logo" width="600"/>
</div>

# NFT Notification Service

> **v1.2 Update (Jan 2026):** Added support for multiple attachments in a single email! Send compressed logs, JSON files, and more.
> 
> **v1.1 Update (Jan 2026):** Fixed 414 URI Too Long error for large email bodies. Now supports unlimited email sizes!

A decoupled, extensible Python notification service for sending rich HTML emails with file attachments using Jenkins as a backend. This service provides a simple `notify()` function that handles everything - from file management to workspace cleanup - making it easy to integrate email notifications into any Python project.

## Table of Contents

- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Architectural Overview](#architectural-overview)
- [Setup Guide](#setup-guide)
  - [Part 1: Jenkins Job Configuration](#part-1-jenkins-job-configuration)
  - [Part 2: Python Module Setup](#part-2-python-module-setup)
- [Usage Examples](#usage-examples)
- [Configuration Reference](#configuration-reference)
- [Workspace Cleanup Strategy](#workspace-cleanup-strategy)
- [Advanced Topics](#advanced-topics)
- [Troubleshooting](#troubleshooting)

## Key Features

- ✅ **Simple API**: Just call `notify(subject, body, attachment_path)` - recipients from config
- ✅ **Multiple Attachments**: Send multiple files in one email (v1.2)
- ✅ **Unique Filenames**: Automatic timestamp+UUID generation prevents concurrent build conflicts
- ✅ **Dual Cleanup**: Both Python and Jenkins clean old files - self-healing system
- ✅ **Decoupled Architecture**: Application unaware of Jenkins implementation
- ✅ **Secure Configuration**: SMTP credentials stored in Jenkins, not in application
- ✅ **Concurrent Build Safe**: Multiple builds can run simultaneously without conflicts
- ✅ **Rich Content**: HTML email bodies and file attachments
- ✅ **Unlimited Email Size**: Supports large HTML reports (100+ KB) without URL length errors (v1.1)
- ✅ **High Compression**: GZIP compression for JSON files (94%+ reduction) (v1.2)
- ✅ **Extensible Backend**: Strategy pattern allows adding new backends (SendGrid, SES, etc.)
- ✅ **Portable Module**: Copy to any project, configure .env, and it works

## Quick Start

### 1. Install the Module

Copy the `notification_service` folder into your project or install as a package.

### 2. Configure `.env`

```env
# Jenkins Connection
JENKINS_URL="http://your-jenkins-server:8080"
JENKINS_USER="your_username"
JENKINS_API_TOKEN="your_api_token"
JENKINS_JOB_NAME="NFT_NOTIFICATION_SERVICE"
JENKINS_BUILD_TOKEN="your_secret_token"
JENKINS_JOB_WORKSPACE="/path/to/jenkins/workspace/JOB_NAME"

# Email Recipients
EMAIL_TO_RECIPIENTS="user1@example.com,user2@example.com"
EMAIL_CC_RECIPIENTS="qa@example.com"
EMAIL_BCC_RECIPIENTS=""

# Workspace Cleanup (optional)
WORKSPACE_CLEANUP_AGE_MINUTES=60
```

### 3. Use in Your Code

```python
import sys
import os
sys.path.insert(0, 'path/to/notification_service')

from notification_service import notify

# Send email with attachment
notify(
    subject="Build Report #42",
    body="<h1>Build Successful!</h1><p>All tests passed.</p>",
    attachment_path="report.txt"
)
```

That's it! Recipients are loaded from `.env`, file is copied to Jenkins workspace, email is sent, and cleanup happens automatically.

## Architectural Overview

### System Design

```
┌─────────────────────┐         ┌──────────────────────┐         ┌─────────────────────┐
│                     │         │  Notification Service│         │                     │
│  Your Application   │────────▶│   (Python Module)    │────────▶│  Jenkins Email Job  │
│                     │         │                      │         │                     │
│  - Calls notify()   │         │  - Manages files     │         │  - Sends email      │
│  - Unaware of       │         │  - Copies to workspace│        │  - Uses SMTP        │
│    Jenkins details  │         │  - Handles cleanup   │         │  - Cleans old files │
└─────────────────────┘         └──────────────────────┘         └─────────────────────┘
         │                                  │                               │
         │                                  │                               │
    Uses simple                       Backend Strategy                SMTP Config
    notify() API                      Pattern separates               stored securely
                                     concerns cleanly                 in Jenkins
```

### File Workflow with Unique Filenames

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         NOTIFICATION WORKFLOW                             │
└──────────────────────────────────────────────────────────────────────────┘

Step 1: Your Application
┌────────────────────────────────┐
│ notify(                         │
│   subject="Build Report",      │
│   body="<h1>Success</h1>",     │
│   attachment_path="report.txt" │
│ )                              │
└────────────────────────────────┘
              │
              ▼
Step 2: Generate Unique Filename
┌────────────────────────────────────────────────┐
│ report.txt →                                    │
│ report_20260103_143052_a1b2c3d4.txt           │
│ (timestamp + UUID ensures uniqueness)          │
└────────────────────────────────────────────────┘
              │
              ▼
Step 3: Cleanup Old Files (Python Layer)
┌────────────────────────────────────────────────┐
│ Scan workspace: Find files >60 min old         │
│ Delete: report_20260103_083000_xxx.txt (old)  │
│ Keep:   report_20260103_142500_yyy.txt (new)  │
└────────────────────────────────────────────────┘
              │
              ▼
Step 4: Copy to Jenkins Workspace
┌────────────────────────────────────────────────┐
│ Source: /app/report.txt                        │
│ Dest:   /jenkins/workspace/                    │
│         report_20260103_143052_a1b2c3d4.txt   │
│ Permissions: 777 (rwxrwxrwx)                   │
└────────────────────────────────────────────────┘
              │
              ▼
Step 5: Trigger Jenkins Job
┌────────────────────────────────────────────────┐
│ POST /job/NFT_NOTIFICATION_SERVICE/build       │
│ Parameters:                                     │
│   ATTACHMENT_PATH=report_20260103_143052...txt │
│   CLEANUP_FILE=report_20260103_143052...txt    │
│   WORKSPACE_CLEANUP_AGE_MINUTES=60             │
│   RECIPIENTS=user@example.com                  │
│   SUBJECT=Build Report                         │
│   BODY=<html>...</html>                        │
└────────────────────────────────────────────────┘
              │
              ▼
Step 6: Jenkins Build Step (Optional)
┌────────────────────────────────────────────────┐
│ Execute shell: Cleanup old files >60 min       │
│ (Redundant cleanup for extra safety)           │
└────────────────────────────────────────────────┘
              │
              ▼
Step 7: Jenkins Sends Email
┌────────────────────────────────────────────────┐
│ - Read file from workspace                     │
│ - Attach to email                              │
│ - Send via SMTP                                │
│ - Log success/failure                          │
└────────────────────────────────────────────────┘
              │
              ▼
Step 8: File Remains in Workspace
┌────────────────────────────────────────────────┐
│ File stays until next cleanup (>60 min old)    │
│ This is SAFE because Jenkins queues jobs       │
└────────────────────────────────────────────────┘
```

### Concurrent Build Safety

```
Time    Build 1                      Build 2                      Build 3
────────────────────────────────────────────────────────────────────────────
12:00   Create report_001.txt
12:00   Copy to workspace
        ├─ Unique: report_20260103_120000_a1b2c3d4.txt
        
12:01                                Create report_002.txt
12:01                                Copy to workspace
                                     ├─ Unique: report_20260103_120100_e5f6g7h8.txt
        
12:02   Jenkins sends email
        Uses: report_20260103_120000_a1b2c3d4.txt ✓
        
12:03                                                             Create report_003.txt
12:03                                                             Copy to workspace
                                                                  ├─ Unique: report_20260103_120300_i9j0k1l2.txt
        
12:04                                Jenkins sends email
                                     Uses: report_20260103_120100_e5f6g7h8.txt ✓
        
12:05                                                             Jenkins sends email
                                                                  Uses: report_20260103_120300_i9j0k1l2.txt ✓
        
Result: All builds succeed - no conflicts! Each has its own unique file.
```

## Setup Guide

### Part 1: Jenkins Job Configuration

#### Step 1: Install Jenkins Plugins

1. Go to **Manage Jenkins** → **Manage Plugins**
2. Install **Email Extension Plugin**
3. Restart Jenkins if required

#### Step 2: Configure SMTP Settings

1. Go to **Manage Jenkins** → **Configure System**
2. Find **Extended E-mail Notification** section
3. Configure SMTP server:
   - SMTP server: `smtp.gmail.com` (or your SMTP server)
   - SMTP port: `587` (for TLS) or `465` (for SSL)
   - Use SMTP Authentication: ✓
   - User Name: Your email
   - Password: App password (NOT your account password)
   - Use SSL/TLS: ✓
4. Test configuration
5. Save

#### Step 3: Create Jenkins Job

1. **Create New Item** → **Freestyle project**
2. Name it: `NFT_NOTIFICATION_SERVICE`
3. Click **OK**

#### Step 4: Configure Job Parameters

In **General** section, check **This project is parameterized**.

Add these parameters (click **Add Parameter** for each):

| Parameter Type | Name | Default Value | Description |
|----------------|------|---------------|-------------|
| String Parameter | `RECIPIENTS` | - | Comma-separated email addresses |
| String Parameter | `SUBJECT` | - | Email subject line |
| Text Parameter | `BODY` | - | Email body (HTML or text) |
| String Parameter | `CONTENT_TYPE` | `text/html` | Content type of email |
| String Parameter | `ATTACHMENT_PATH` | - | Filename in workspace to attach |
| String Parameter | `CLEANUP_FILE` | - | File to clean up (if using post-build cleanup) |
| String Parameter | `WORKSPACE_CLEANUP_AGE_MINUTES` | `60` | Age threshold for cleanup |

#### Step 5: Enable Remote Build Trigger

1. In **Build Triggers** section
2. Check **Trigger builds remotely (e.g., from scripts)**
3. **Authentication Token**: Enter a strong random string (save this as `JENKINS_BUILD_TOKEN`)

#### Step 6: Add Build Step for Cleanup (Recommended)

**Why**: If you send emails in post-build actions, add this as the FIRST build step.

1. Click **Add build step** → **Execute shell**
2. Paste this script:

```bash
# Cleanup old attachment files (from previous runs)
CLEANUP_AGE="${WORKSPACE_CLEANUP_AGE_MINUTES:-60}"
echo "Cleaning up attachment files older than ${CLEANUP_AGE} minutes..."
find "${WORKSPACE}" -maxdepth 1 -type f -name "*_????????_??????_*.*" -mmin "+${CLEANUP_AGE}" -exec rm -f {} \; -print
echo "Cleanup complete"
```

**What this does**:
- Runs BEFORE email is sent
- Cleans files >60 min old from previous runs
- Current file is safe (hasn't been created yet)
- Provides redundant cleanup layer

#### Step 7: Configure Post-build Action (Email)

1. Click **Add post-build action** → **Editable Email Notification**
2. Click **Advanced Settings...**
3. Configure fields:
   - **Project Recipient List**: `$RECIPIENTS`
   - **Default Subject**: `$SUBJECT`
   - **Default Content**: `$BODY`
   - **Content Type**: Select `HTML (text/html)` from dropdown
   - **Attachments**: `$ATTACHMENT_PATH`
4. Add **Trigger**: Click **Add Trigger** → **Always**
5. Save the job

#### Complete Jenkins Job Structure

```
Job: NFT_NOTIFICATION_SERVICE

Parameters:
  ✓ RECIPIENTS (string)
  ✓ SUBJECT (string)
  ✓ BODY (text)
  ✓ CONTENT_TYPE (string) = "text/html"
  ✓ ATTACHMENT_PATH (string)
  ✓ CLEANUP_FILE (string)
  ✓ WORKSPACE_CLEANUP_AGE_MINUTES (string) = "60"

Build Triggers:
  ✓ Trigger builds remotely
    Token: <your_secret_token>

Build Steps:
  1. Execute shell: Cleanup old files
     └─ Removes files >60 min old

Post-build Actions:
  ✓ Editable Email Notification
    Recipients: $RECIPIENTS
    Subject: $SUBJECT
    Content: $BODY
    Attachments: $ATTACHMENT_PATH
    Trigger: Always
```

### Part 2: Python Module Setup

#### Step 1: Copy Module to Your Project

```bash
your_project/
├── notification_service/          # Copy this entire folder
│   ├── __init__.py
│   ├── client.py
│   ├── config.py
│   ├── models.py
│   ├── notify.py
│   ├── exceptions.py
│   └── backends/
│       ├── __init__.py
│       ├── base.py
│       └── jenkins_backend.py
├── .env                           # Create this
└── your_script.py                 # Your code
```

#### Step 2: Install Dependencies

```bash
pip install python-dotenv requests
```

Or create `requirements.txt`:
```txt
python-dotenv>=0.19.0
requests>=2.26.0
```

#### Step 3: Create `.env` Configuration

```env
# .env - Jenkins Connection Details
JENKINS_URL="your_jenkins_url"     # http://0.0.0.0:8080
JENKINS_USER="your_jenkins_user"             # username
JENKINS_API_TOKEN="your_jenkins_api_token"
JENKINS_JOB_NAME="your_jenkins_job_name"
JENKINS_BUILD_TOKEN="your_jenkins_build_token"
JENKINS_JOB_WORKSPACE="your_jenkins_workspace"

# Email Recipients Configuration
EMAIL_TO_RECIPIENTS="user1@example.com,user2@example.com"
EMAIL_CC_RECIPIENTS="qa@example.com,manager@example.com"
EMAIL_BCC_RECIPIENTS=""

# Workspace Cleanup Configuration (optional, default: 60)
WORKSPACE_CLEANUP_AGE_MINUTES=60
```

**How to get these values:**
- `JENKINS_URL`: Your Jenkins server URL
- `JENKINS_USER`: Your Jenkins username
- `JENKINS_API_TOKEN`: Generate from **Jenkins** → **User** → **Configure** → **API Token** → **Add new Token**
- `JENKINS_BUILD_TOKEN`: The token you set in Step 5 of Jenkins configuration
- `JENKINS_JOB_WORKSPACE`: Find this in Jenkins job's workspace page

## Usage Examples

### Example 1: Simple Notification (No Attachment)

```python
import sys
sys.path.insert(0, 'path/to/notification_service')

from notification_service import notify

notify(
    subject="Deployment Successful",
    body="<h1>✓ Production Deployment Complete</h1><p>All services are running.</p>"
)
```

### Example 2: Notification with Attachment

```python
import sys
import os
sys.path.insert(0, 'path/to/notification_service')

from notification_service import notify

# Create a report file
with open("build_report.txt", "w") as f:
    f.write("Build #42 completed successfully\n")
    f.write("All tests passed: 156/156\n")

try:
    notify(
        subject="Build Report #42",
        body="<h1>Build Successful</h1><p>See attached report.</p>",
        attachment_path="build_report.txt"
    )
    print("✓ Email sent successfully!")
finally:
    # Cleanup local file
    os.remove("build_report.txt")
```

### Example 3: Multiple Attachments (v1.2)

```python
import sys
sys.path.insert(0, 'path/to/notification_service')

from notification_service import NotificationClient, EmailRequest

# Create multiple files to attach
import gzip
import json

# Create compressed JSON file
data = {"test": "results", "passed": 42, "failed": 0}
with gzip.open("test_results.json.gz", "wb", compresslevel=9) as f:
    f.write(json.dumps(data, indent=2).encode('utf-8'))

# Create a log archive
with open("debug.log", "w") as f:
    f.write("Debug logs content here\n")

try:
    client = NotificationClient()
    email = EmailRequest(
        to_recipients=["team@example.com"],
        subject="Test Results",
        body="<h1>Test Complete</h1><p>See attached files.</p>",
        attachment_paths=["test_results.json.gz", "debug.log"]  # Multiple files
    )
    client.send_email(email)
    print("✓ Email with multiple attachments sent!")
finally:
    import os
    os.remove("test_results.json.gz")
    os.remove("debug.log")
```

### Example 4: Plain Text Email

```python
from notification_service import notify

notify(
    subject="Server Alert",
    body="Warning: Disk usage at 85%\nPlease investigate.",
    content_type="text/plain"
)
```

### Example 4: Dynamic HTML Report

```python
from notification_service import notify

# Generate test results
tests_passed = 156
tests_total = 156
coverage = 94.5

html_body = f"""
<html>
<head>
    <style>
        .success {{ color: green; font-weight: bold; }}
        .metric {{ background: #f0f0f0; padding: 10px; margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>Test Execution Report</h1>
    <div class="metric">
        <strong>Status:</strong> <span class="success">✓ PASSED</span>
    </div>
    <div class="metric">
        <strong>Tests:</strong> {tests_passed}/{tests_total}
    </div>
    <div class="metric">
        <strong>Coverage:</strong> {coverage}%
    </div>
</body>
</html>
"""

notify(
    subject="Test Report - All Tests Passed",
    body=html_body
)
```

### Example 5: Advanced Usage with Error Handling

```python
from notification_service import notify, BackendError
import logging

def send_build_notification(build_number, status, log_file):
    """Send build notification with comprehensive error handling"""
    
    try:
        subject = f"Build #{build_number} - {status}"
        
        body = f"""
        <html>
        <body>
            <h1>Build #{build_number}</h1>
            <p><strong>Status:</strong> {status}</p>
            <p>See attached logs for details.</p>
        </body>
        </html>
        """
        
        notify(
            subject=subject,
            body=body,
            attachment_path=log_file
        )
        
        logging.info(f"Build notification sent for build #{build_number}")
        return True
        
    except BackendError as e:
        logging.error(f"Failed to send notification: {e}")
        # Fallback: Log to file
        with open("failed_notifications.log", "a") as f:
            f.write(f"Build #{build_number}: {str(e)}\n")
        return False
        
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        return False
```

### Example 6: Using Original Interface (Advanced)

If you need more control over recipients:

```python
from notification_service import NotificationClient, EmailRequest

client = NotificationClient()

email = EmailRequest(
    to_recipients=["custom@example.com"],
    cc_recipients=["team@example.com"],
    bcc_recipients=["archive@example.com"],
    subject="Custom Notification",
    body="<h1>Custom HTML</h1>",
    content_type="text/html",
    attachment_path="report.pdf"
)

client.send_email(email)
```

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JENKINS_URL` | Yes | - | Base URL of Jenkins server |
| `JENKINS_USER` | Yes | - | Jenkins username with build permissions |
| `JENKINS_API_TOKEN` | Yes | - | API token (not password!) |
| `JENKINS_JOB_NAME` | Yes | - | Name of Jenkins job to trigger |
| `JENKINS_BUILD_TOKEN` | Yes | - | Remote build trigger token |
| `JENKINS_JOB_WORKSPACE` | Yes | - | Full path to Jenkins workspace |
| `EMAIL_TO_RECIPIENTS` | Yes | - | Comma-separated TO recipients |
| `EMAIL_CC_RECIPIENTS` | No | `""` | Comma-separated CC recipients |
| `EMAIL_BCC_RECIPIENTS` | No | `""` | Comma-separated BCC recipients |
| `WORKSPACE_CLEANUP_AGE_MINUTES` | No | `60` | Age threshold for file cleanup |

### Unique Filename Format

Each attachment gets a unique filename:

```
Format: basename_YYYYMMDD_HHMMSS_UUID.ext

Examples:
report.txt        → report_20260103_143052_a1b2c3d4.txt
results.pdf       → results_20260103_143052_e5f6g7h8.pdf
test_logs.tar.gz  → test_logs_20260103_143052_i9j0k1l2.tar.gz

Components:
- basename: Original filename without extension
- YYYYMMDD: Date (20260103 = Jan 3, 2026)
- HHMMSS: Time (143052 = 14:30:52 or 2:30:52 PM)
- UUID: First 8 chars of UUID4 (a1b2c3d4)
- .ext: Original file extension
```

**Benefits:**
- **Sortable**: Timestamp allows chronological sorting
- **Traceable**: Know exact creation time from filename
- **Unique**: UUID prevents collisions in concurrent builds
- **Pattern-matchable**: Can cleanup using glob patterns

## Workspace Cleanup Strategy

### Dual-Layer Cleanup Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DUAL CLEANUP PROTECTION                       │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Python Notification Service
┌────────────────────────────────────────────────────────────────┐
│ When: Before copying new file                                   │
│ What: Scans workspace, deletes files >60 min old              │
│ How:  _cleanup_old_files() method in jenkins_backend.py       │
│ Advantage: Cleans BEFORE Jenkins starts                       │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Layer 2: Jenkins Build Step (Optional but Recommended)
┌────────────────────────────────────────────────────────────────┐
│ When: First build step (before email)                         │
│ What: Scans workspace, deletes files >60 min old              │
│ How:  Shell script using find -mmin                           │
│ Advantage: Catches files if Python couldn't access workspace  │
└────────────────────────────────────────────────────────────────┘

Result: Even if one layer fails, the other provides protection!
```

### Why This Works

**Problem**: Jenkins queues jobs, so immediate cleanup would delete files before use.

**Solution**: Cleanup happens BEFORE new file is created:

```
Timeline:
12:00:00  - Job triggered, cleanup runs (deletes files >60 min old)
12:00:01  - New file copied: report_20260103_120001_xxx.txt (0 min old)
12:00:02  - Email sent with new file (still < 1 min old)
12:00:03  - New file remains in workspace
...
13:01:00  - Next job runs, now previous file is >60 min old
13:01:01  - Cleanup deletes the old file
13:01:02  - New file created for current notification
```

**Current file is ALWAYS safe because:**
1. Cleanup runs first (old files deleted)
2. New file created after cleanup (timestamp is NOW)
3. Email sent immediately (file is fresh)
4. File stays until next run (when it becomes old)

### Configuration Options

```env
# Age threshold in minutes (default: 60)
WORKSPACE_CLEANUP_AGE_MINUTES=60

# Examples of different thresholds:
# WORKSPACE_CLEANUP_AGE_MINUTES=30   # Aggressive (30 min)
# WORKSPACE_CLEANUP_AGE_MINUTES=120  # Conservative (2 hours)
# WORKSPACE_CLEANUP_AGE_MINUTES=1440 # Very conservative (24 hours)
```

### Cleanup Methods Comparison

| Method | Location | When | Pros | Cons |
|--------|----------|------|------|------|
| **Python** | notification_service | Before copy | Fast, runs before Jenkins | Needs workspace access |
| **Jenkins Build Step** | Jenkins job | First build step | Always has access | Requires job config |
| **Jenkins Post-build** | Jenkins job | After email | Traditional approach | Doesn't work with post-build email |

**Recommendation**: Use both Python + Jenkins Build Step for maximum reliability.

## Advanced Topics

### Multiple Attachments (v1.2)

You can send multiple files in a single email by using the `attachment_paths` parameter:

```python
from notification_service import NotificationClient, EmailRequest

client = NotificationClient()
email = EmailRequest(
    to_recipients=["team@example.com"],
    subject="Multiple Reports",
    body="<h1>Daily Reports</h1><p>See attached files.</p>",
    attachment_paths=[
        "failed_steps.json.gz",  # Compressed JSON
        "logs_20260103.zip",      # Log archive
        "summary_report.txt"      # Text summary
    ]
)
client.send_email(email)
```

**Key Points:**
- Uses `attachment_paths` (plural) instead of `attachment_path` (singular)
- Jenkins Email Extension plugin handles comma-separated attachment paths
- All files are copied to Jenkins workspace with unique names
- Automatic cleanup of all attachment files after email is sent

**Backward Compatibility:**
The single `attachment_path` parameter still works for single file attachments.

### Extending with New Backends

The service uses the Strategy Pattern, making it easy to add new backends:

```python
# backends/sendgrid_backend.py
from .base import BaseBackend
from ..models import EmailRequest
from ..exceptions import BackendError
import sendgrid

class SendGridBackend(BaseBackend):
    def __init__(self, settings):
        self.api_key = settings.SENDGRID_API_KEY
        self.sg = sendgrid.SendGridAPIClient(self.api_key)
    
    def send(self, email_request: EmailRequest) -> None:
        # Implement SendGrid API call
        message = sendgrid.Mail(
            from_email='sender@example.com',
            to_emails=email_request.to_recipients,
            subject=email_request.subject,
            html_content=email_request.body
        )
        
        if email_request.attachment_path or email_request.attachment_paths:
            # Add attachment logic for single or multiple attachments
            for attachment in email_request.get_all_attachments():
                # Process each attachment
                pass
        
        try:
            response = self.sg.send(message)
            print(f"Email sent via SendGrid: {response.status_code}")
        except Exception as e:
            raise BackendError(f"SendGrid failed: {e}") from e
```

**Usage:**
```python
from notification_service import NotificationClient
from notification_service.backends.sendgrid_backend import SendGridBackend

backend = SendGridBackend(settings)
client = NotificationClient(backend=backend)
client.send_email(email_request)
```

### Custom Notification Wrapper

Create a project-specific wrapper:

```python
# my_notifications.py
from notification_service import notify, BackendError
import logging

class ProjectNotifier:
    def __init__(self, project_name):
        self.project_name = project_name
        self.logger = logging.getLogger(__name__)
    
    def send_success(self, message, attachment=None):
        """Send success notification"""
        subject = f"[{self.project_name}] ✓ Success"
        body = f"<h1 style='color:green'>Success</h1><p>{message}</p>"
        self._send(subject, body, attachment)
    
    def send_failure(self, message, attachment=None):
        """Send failure notification"""
        subject = f"[{self.project_name}] ✗ Failure"
        body = f"<h1 style='color:red'>Failure</h1><p>{message}</p>"
        self._send(subject, body, attachment)
    
    def _send(self, subject, body, attachment):
        try:
            notify(subject=subject, body=body, attachment_path=attachment)
            self.logger.info(f"Notification sent: {subject}")
        except BackendError as e:
            self.logger.error(f"Notification failed: {e}")

# Usage
notifier = ProjectNotifier("Alpha Project")
notifier.send_success("Build completed!", "build_log.txt")
```

## Troubleshooting

### Common Issues

#### 1. `403 Forbidden` Error

**Symptoms:**
```
BackendError: HTTP request to Jenkins failed: 403 Client Error: Forbidden
```

**Solutions:**
- ✅ Check `JENKINS_API_TOKEN` is an **API token**, not password
  - Generate: Jenkins → User → Configure → API Token → Add new Token
- ✅ Verify user has **Job/Build** permissions for the job
- ✅ Check `JENKINS_BUILD_TOKEN` matches job configuration
- ✅ Ensure remote build trigger is enabled in job

#### 2. Files Not Attaching

**Symptoms:**
- Email sends but no attachment
- Jenkins log shows "file not found"

**Solutions:**
- ✅ Check `JENKINS_JOB_WORKSPACE` path is correct
  - Find in Jenkins: Job → Workspace → Check URL/path
- ✅ Verify file exists in workspace before email sends
  - Add build step to list workspace: `ls -la ${WORKSPACE}`
- ✅ Check `ATTACHMENT_PATH` parameter matches filename
- ✅ Verify Jenkins has read permissions on workspace files

#### 3. Old Files Accumulating

**Symptoms:**
- Workspace fills with old attachment files
- Cleanup not working

**Solutions:**
- ✅ Verify `WORKSPACE_CLEANUP_AGE_MINUTES` is set in .env
- ✅ Check Python cleanup runs (look for cleanup logs)
- ✅ Add Jenkins build step cleanup (if not already added)
- ✅ Manually check file timestamps: `ls -lt ${WORKSPACE}`
- ✅ Verify glob pattern matches: `*_????????_??????_*.*`

#### 4. Concurrent Builds Failing

**Symptoms:**
- One build succeeds, others fail
- Attachment conflicts

**Solutions:**
- ✅ Verify unique filenames are being generated
  - Check logs for filename like: `report_20260103_143052_a1b2c3d4.txt`
- ✅ Ensure cleanup isn't deleting new files
  - New files should be <1 min old, safe from cleanup
- ✅ Check workspace has enough space
- ✅ Verify no file locking issues

#### 5. `ValueError: No TO recipients configured`

**Symptoms:**
```
ValueError: No TO recipients configured. Please set EMAIL_TO_RECIPIENTS in .env file.
```

**Solutions:**
- ✅ Add `EMAIL_TO_RECIPIENTS` to .env file
- ✅ Ensure .env is in correct directory
- ✅ Check .env file is not named .env.txt or similar
- ✅ Verify no typos in variable name

#### 6. Workspace Not Found Error

**Symptoms:**
```
BackendError: Jenkins workspace directory does not exist: /path/to/workspace
```

**Solutions:**
- ✅ Run Jenkins job at least once to create workspace
- ✅ Check `JENKINS_JOB_WORKSPACE` path in .env
- ✅ Verify path with: `ls -la /path/to/workspace`
- ✅ Ensure Jenkins user has access to workspace directory

#### 7. `414 URI Too Long` Error (FIXED in v1.1)

**Symptoms:**
```
BackendError: HTTP request to Jenkins failed: 414 Client Error: URI Too Long
```

**Cause:**
Large HTML email bodies (75+ KB) exceeded Jenkins URL length limits when sent as URL parameters.

**Solution (Applied Automatically):**
✅ **Fixed in version 1.1** - The notification service now sends only the token as a URL parameter and everything else (including large HTML bodies) in the POST request body.

**Technical Details:**
- **Before:** All parameters sent in URL → 100+ KB URLs → 414 Error
- **After:** Only token in URL (~18 bytes), body in POST data → No limit
- **Compatibility:** Fully backward compatible with all Jenkins jobs
- **No changes needed:** Your code and Jenkins configuration work as-is

**If you still see this error:**
- Verify you're using the latest version (v1.1+)
- Check that `jenkins_backend.py` contains the fix:
  ```bash
  grep -A 3 "Separate token" notification_service/backends/jenkins_backend.py
  ```
- Should show: `token = params.pop("token")`

**Performance:**
- Email body size: Unlimited (tested with 100+ KB)
- URL size: ~18 bytes (only token)
- Speed: No performance impact

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from notification_service import notify

# Now you'll see detailed debug output
notify(subject="Test", body="<h1>Debug Test</h1>")
```

### Testing Cleanup

Manually test cleanup logic:

```bash
# Create test files with old timestamps
cd /path/to/jenkins/workspace
touch -t 202601030800 test_file_20260103_080000_xxxxxxxx.txt

# Run notification (should clean old file)
python your_script.py

# Check if old file was deleted
ls -la test_file_*
```

## Project Structure

```
notification_service/
├── __init__.py              # Exports notify(), NotificationClient, etc.
├── notify.py                # Simple notify() function
├── client.py                # NotificationClient class
├── config.py                # Settings loader
├── models.py                # EmailRequest data model
├── exceptions.py            # Custom exceptions
└── backends/
    ├── __init__.py
    ├── base.py             # BaseBackend abstract class
    └── jenkins_backend.py  # Jenkins implementation
        ├── _generate_unique_filename()
        ├── _cleanup_old_files()
        ├── _copy_to_workspace()
        └── send()
```

## Performance Considerations

- **Workspace Scan**: Cleanup scans workspace files - ~O(n) where n = files
- **Concurrent Builds**: No locking needed - unique filenames prevent conflicts
- **Jenkins Queue**: Jobs queue gracefully - Jenkins manages concurrency
- **File Copy**: ~O(1) for single file copy operation
- **Network**: HTTP POST to Jenkins - depends on body size

## Security Considerations

- ✅ **SMTP Credentials**: Stored in Jenkins, not in application
- ✅ **API Tokens**: Use Jenkins API tokens, never passwords
- ✅ **Build Tokens**: Keep `JENKINS_BUILD_TOKEN` secret
- ✅ **File Permissions**: Files created with 777 for Jenkins access
- ✅ **Workspace Isolation**: Each job has separate workspace
- ✅ **No Code Injection**: Parameters are passed as strings, not executed

## License

Internal use - NFT Automations Project

---
