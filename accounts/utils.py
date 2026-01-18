from django.core.cache import cache
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import random

OTP_TIMEOUT = 300


def generate_otp():
    """Generate 6-digit numeric OTP"""
    return str(random.randint(100000, 999999))


def set_otp_cache(user_id, otp):
    """Store OTP in cache"""
    cache.set(f"otp_{user_id}", otp, timeout=OTP_TIMEOUT)


def get_otp_cache(user_id):
    return cache.get(f"otp_{user_id}")


def delete_otp_cache(user_id):
    cache.delete(f"otp_{user_id}")


EMAIL_SUBJECTS = {
    "verify_email": "🔐 Verify your email",
    "forgot_password": "🔁 Reset your password",
}


def send_otp_email(to_email, otp, purpose="verify_email"):

    subject = EMAIL_SUBJECTS.get(purpose, "OTP Verification")

    html_content = render_to_string(
        "emails/verify_email.html", {"OTP": otp, "subject": subject}
    )

    email = EmailMessage(
        subject=subject,
        body=html_content,
        to=[to_email],
    )
    email.content_subtype = "html"
    email.send()
