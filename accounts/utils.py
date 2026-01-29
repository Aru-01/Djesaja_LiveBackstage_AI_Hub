from accounts.models import OTP
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
import random


def generate_otp():
    return str(random.randint(100000, 999999))


def can_resend_otp(user, purpose):
    last_otp = (
        OTP.objects.filter(user=user, purpose=purpose).order_by("-created_at").first()
    )
    if not last_otp:
        return True

    return timezone.now() > last_otp.created_at + timedelta(seconds=30)


def create_otp(user, purpose):
    OTP.objects.filter(user=user, purpose=purpose).delete()

    return OTP.objects.create(
        user=user,
        code=generate_otp(),
        purpose=purpose,
    )


def verify_otp(user, otp, purpose):
    otp_obj = OTP.objects.filter(user=user, code=otp, purpose=purpose).first()

    if not otp_obj:
        return False, "Invalid OTP"

    if otp_obj.is_expired():
        otp_obj.delete()
        return False, "OTP expired"

    otp_obj.delete()
    return True, "OTP verified"


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
