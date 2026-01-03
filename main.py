# main.py
import os
from notification_service import NotificationClient, EmailRequest, BackendError


def create_dummy_attachment(filename="report.txt"):
    """Creates a simple file to use as an attachment."""
    with open(filename, "w") as f:
        f.write("This is a test report.\n")
    return os.path.abspath(filename)


def run_main_process():
    """
    Simulates the main application logic that needs to send an email.
    """
    print("--- Starting main application process ---")

    # 1. Initialize the notification client
    client = NotificationClient()

    # 2. Create a dummy file to attach
    attachment_path = create_dummy_attachment()

    # 3. Prepare the email content dynamically
    html_body = """
    <html>
    <body>
        <h1>Project Alpha - Build Report</h1>
        <p>The scheduled build has completed successfully.</p>
        <p>Please find the detailed results in the attached report.</p>
        <p><b>Status:</b> <span style='color:green;'>SUCCESS</span></p>
    </body>
    </html>
    """

    # 4. Create an EmailRequest object
    email = EmailRequest(
        to_recipients=["email@example.com", "mail@example.com"],
        cc_recipients=["email@example.com"],
        subject="Project Alpha - Nightly Build Report",
        body=html_body,
        attachment_path=attachment_path,
    )

    # 5. Send the email via the service
    try:
        print("Attempting to send email via Notification Service...")
        client.send_email(email)
        print("--- Email dispatch command sent successfully! ---")
    except BackendError as e:
        print("\nERROR: Failed to send notification.")
        print(f"Reason: {e}")
        # Here you could add fallback logic, e.g., log to a file or try another service.
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

    finally:
        # Clean up the dummy file
        os.remove(attachment_path)


if __name__ == "__main__":
    run_main_process()
