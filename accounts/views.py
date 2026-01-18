from rest_framework import generics, permissions
from rest_framework.views import APIView
from accounts.models import User
from accounts.serializers import (
    UserSerializer,
    SelfProfileUpdateSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ResendOtpSerializer,
    VerifyOtpSerializer,
)
from rest_framework.response import Response
from rest_framework import status, permissions
from accounts.utils import (
    send_otp_email,
    generate_otp,
    set_otp_cache,
    get_otp_cache,
    delete_otp_cache,
)


# Create your views here.
class SelfProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class SelfProfileUpdateView(generics.UpdateAPIView):
    serializer_class = SelfProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class SendEmailOtpView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        email = request.data.get("email")

        if not email:
            return Response({"detail": "Email required"}, status=400)
        if user.email_verified:
            return Response({"detail": "Email already verified"}, status=400)

        # Save email temporarily
        user.email = email
        user.email_verified = False
        user.save()

        otp = generate_otp()
        set_otp_cache(user.id, otp)
        send_otp_email(email, otp, "verify_email")

        return Response({"detail": "OTP sent to email"}, status=200)


class VerifyEmailOtpView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        otp = request.data.get("otp")
        cached_otp = get_otp_cache(user.id)

        if not cached_otp:
            return Response({"detail": "OTP expired"}, status=400)
        if otp != cached_otp:
            return Response({"detail": "Invalid OTP"}, status=400)

        user.email_verified = True
        user.save()
        delete_otp_cache(user.id)

        return Response({"detail": "Email verified successfully"}, status=200)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password changed successfully"}, status=status.HTTP_200_OK
        )


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)


class VerifyOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OTP verified"}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password reset successfully"}, status=status.HTTP_200_OK
        )


class ResendOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)
