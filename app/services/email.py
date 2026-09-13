import os
import resend


# ---------------------------
# Resend email config
# ---------------------------
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# Set in Railway as:
# FROM_EMAIL=CopStopSD <noreply@copstopsd.org>
FROM_EMAIL = os.getenv(
    "FROM_EMAIL",
    "CopStopSD <noreply@copstopsd.org>"
)

# Email address that receives new complaint notifications
STAFF_NOTIFICATION_EMAIL = os.getenv("STAFF_NOTIFICATION_EMAIL")


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

    _send_email(subject, to_email, body)


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

    if not STAFF_NOTIFICATION_EMAIL:
        raise RuntimeError(
            "STAFF_NOTIFICATION_EMAIL must be set in environment variables"
        )

    _send_email(
        subject,
        STAFF_NOTIFICATION_EMAIL,
        body
    )

