from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import (
    SelfProfileView,
    SelfProfileUpdateView,
    ChangePasswordView,
    SendEmailOtpView,
    VerifyEmailOtpView,
    ForgotPasswordView,
    VerifyOtpView,
    ResetPasswordView,
    ResendOtpView,
)

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", SelfProfileView.as_view(), name="self_profile"),
    path("me/update/", SelfProfileUpdateView.as_view(), name="self_profile_update"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("me/send-email-otp/", SendEmailOtpView.as_view(), name="send_email_otp"),
    path("me/verify-email-otp/", VerifyEmailOtpView.as_view(), name="verify_email_otp"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("verify-otp/", VerifyOtpView.as_view(), name="verify_otp"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path("resend-otp/", ResendOtpView.as_view(), name="resend_otp"),
]
