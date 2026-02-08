import os
import smtplib
from email.message import EmailMessage

# ---------------------------
# Email config (ALL via env vars)
# ---------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Required (set these in Railway Variables)
SMTP_USER = os.getenv("SMTP_USER")  # e.g. laila@potcsd.org
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Google App Password (16 chars)

# Optional
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)


def _send_email(subject: str, to_email: str, body: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in environment variables")

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    # STARTTLS (recommended for Gmail)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


# ---------------------------
# OTP EMAIL (2FA)
# ---------------------------
def send_otp_email(to_email: str, otp_code: str) -> None:
    subject = "Your CopStopSD verification code"
    body = f"""Your verification code is:

{otp_code}

This code will expire in 10 minutes.

If you did not request this code, you can ignore this email.
"""
    _send_email(subject, to_email, body)


# ---------------------------
# Existing notification email
# ---------------------------
def send_new_submission_email(case_number: str, summary: str, link: str) -> None:
    subject = f"New Complaint Submitted — Case {case_number}"
    body = f"""A new complaint has been submitted.

Case Number:
{case_number}

Summary:
{summary}

View complaint:
{link}
"""
    staff_email = os.getenv("STAFF_NOTIFICATION_EMAIL") or SMTP_USER
    if not staff_email:
        raise RuntimeError("STAFF_NOTIFICATION_EMAIL not configured (or SMTP_USER missing)")

    _send_email(subject, staff_email, body)

