import os
import smtplib
from email.message import EmailMessage


# ---------------------------
# Email config
# ---------------------------
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=laila@potcsd.org
SMTP_PASS=gzup tsnm lods mcwa
EMAIL_FROM=laila@potcsd.org



def _send_email(subject: str, to_email: str, body: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USER and SMTP_PASSWORD must be set in environment variables"
        )

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


# ---------------------------
# OTP EMAIL (2FA)
# ---------------------------
def send_otp_email(to_email: str, otp_code: str) -> None:
    subject = "Your verification code"
    body = f"""
Your verification code is:

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
    body = f"""
A new complaint has been submitted.

Case Number:
{case_number}

Summary:
{summary}

View complaint:
{link}
"""
    # Change this to the staff email(s) you want notified
    staff_email = os.getenv("STAFF_NOTIFICATION_EMAIL", SMTP_USER)
    if not staff_email:
        raise RuntimeError("STAFF_NOTIFICATION_EMAIL not configured")

    _send_email(subject, staff_email, body)
