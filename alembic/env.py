import os

# ---------------------------
# SECURITY
# ---------------------------
os.environ.setdefault("SECRET_KEY", "dev-change-this-secret")

# ✅ Public intake key (for mobile app / public form)
# Change this to a long random string in production.
os.environ.setdefault("PUBLIC_INTAKE_KEY", "dev-public-intake-key-change-me")

# ✅ Simple rate limiting (per IP)
# max requests allowed per window per IP
os.environ.setdefault("PUBLIC_INTAKE_RATE_LIMIT_MAX", "10")
# window length in seconds
os.environ.setdefault("PUBLIC_INTAKE_RATE_LIMIT_WINDOW_SECONDS", "60")

# ---------------------------
# EMAIL (SMTP)
# ---------------------------
os.environ.setdefault("SMTP_HOST", "smtp.gmail.com")
os.environ.setdefault("SMTP_PORT", "587")

# CHANGE THESE 👇
os.environ.setdefault("SMTP_USER", "your_email@gmail.com")
os.environ.setdefault("SMTP_PASSWORD", "your_gmail_app_password")

os.environ.setdefault("FROM_EMAIL", os.environ.get("SMTP_USER", ""))
os.environ.setdefault("STAFF_NOTIFICATION_EMAIL", "alerts@yourorg.org")

# ✅ Password reset code expiry
os.environ.setdefault("RESET_OTP_EXPIRE_MINUTES", "10")
