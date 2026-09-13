import os
import resend


# ---------------------------
# Resend email config
# ---------------------------

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

FROM_EMAIL = os.getenv(
    "FROM_EMAIL",
    "CopStopSD <noreply@copstopsd.org>"
)

# Comma-separated list in Railway, for example:
# laila@potcsd.org,staff1@potcsd.org,staff2@potcsd.org
STAFF_NOTIFICATION_EMAILS = [
    email.strip()
    for email in os.getenv("STAFF_NOTIFICATION_EMAILS", "").split(",")
    if email.strip()
]


# ---------------------------
# Base email sender
# ---------------------------

def _send_email(subject: str, to_email: str, body: str) -> None:
    if not RESEND_API_KEY:
        raise RuntimeError(
            "RESEND_API_KEY must be set in environment variables"
        )

    resend.api_key = RESEND_API_KEY

    response = resend.Emails.send({
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "text": body,
    })

    print(f"[RESEND] Email sent to {to_email}: {response}")


# ---------------------------
# OTP EMAIL (2FA)
# ---------------------------

def send_otp_email(to_email: str, otp_code: str) -> None:
    subject = "Your CopStopSD verification code"

    body = f"""Your CopStopSD verification code is:

{otp_code}

This code will expire in 10 minutes.

If you did not request this code, you can ignore this email.
"""

    _send_email(
        subject,
        to_email,
        body
    )


# ---------------------------
# Complaint notification email
# ---------------------------

def send_new_submission_email(
    case_number: str,
    summary: str,
    link: str
) -> None:

    subject = f"New Complaint Submitted — Case {case_number}"

    body = f"""A new complaint has been submitted.

Case Number:
{case_number}

Summary:
{summary}

View complaint:
{link}
"""

    if not STAFF_NOTIFICATION_EMAILS:
        raise RuntimeError(
            "STAFF_NOTIFICATION_EMAILS must be set in environment variables"
        )

    for staff_email in STAFF_NOTIFICATION_EMAILS:
        _send_email(
            subject,
            staff_email,
            body
        )

