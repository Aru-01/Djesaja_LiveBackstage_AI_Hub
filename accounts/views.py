from rest_framework import generics, permissions
from rest_framework.views import APIView
from accounts.serializers import (
    UserSerializer,
    SelfProfileUpdateSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ResendOtpSerializer,
    VerifyOtpSerializer,
    MyTokenObtainPairSerializer,
)
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from accounts.utils import create_otp, can_resend_otp, send_otp_email, verify_otp
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="User Login (JWT Token)",
        tags=["Authentication"],
        request_body=MyTokenObtainPairSerializer,
        responses={200: "JWT access & refresh token", 401: "Invalid credentials"},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SelfProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Logged-in User Profile",
        tags=["Profile"],
        responses={200: UserSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class SelfProfileUpdateView(generics.UpdateAPIView):
    serializer_class = SelfProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update Logged-in User Profile",
        tags=["Profile"],
        request_body=SelfProfileUpdateSerializer,
        responses={200: UserSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class SendEmailOtpView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Send OTP to Email for Verification",
        tags=["Profile"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
            },
        ),
        responses={
            200: "OTP sent to email",
            400: "Email required / Already verified",
        },
    )
    def post(self, request):
        user = request.user
        email = request.data.get("email")

        if not email:
            return Response({"detail": "Email required"}, status=400)

        if user.email_verified:
            return Response({"detail": "Email already verified"}, status=400)

        if not can_resend_otp(user, "verify_email"):
            return Response(
                {"detail": "Please wait 30 seconds before resending OTP"},
                status=400,
            )

        user.email = email
        user.email_verified = False
        user.save()

        otp_obj = create_otp(user, "verify_email")
        send_otp_email(email, otp_obj.code, "verify_email")

        return Response({"detail": "OTP sent to email"}, status=200)


class VerifyEmailOtpView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Verify Email OTP",
        tags=["Profile"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["otp"],
            properties={
                "otp": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: "Email verified successfully",
            400: "Invalid / Expired OTP",
        },
    )
    def post(self, request):
        user = request.user
        otp = request.data.get("otp")

        is_valid, message = verify_otp(user, otp, "verify_email")

        if not is_valid:
            return Response({"detail": message}, status=400)

        user.email_verified = True
        user.save()

        return Response({"detail": "Email verified successfully"}, status=200)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Change Password (Authenticated User)",
        tags=["Profile"],
        request_body=ChangePasswordSerializer,
        responses={
            200: "Password changed successfully",
            400: "Validation error",
        },
    )
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

    @swagger_auto_schema(
        operation_summary="Forgot Password - Send OTP",
        tags=["Password Recovery"],
        request_body=ForgotPasswordSerializer,
        responses={
            200: "OTP sent to email",
            400: "Invalid email",
        },
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)


class VerifyOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Verify OTP for Password Reset",
        tags=["Password Recovery"],
        request_body=VerifyOtpSerializer,
        responses={
            200: "OTP verified",
            400: "Invalid / Expired OTP",
        },
    )
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "OTP verified"}, status=200)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Reset Password Using OTP",
        tags=["Password Recovery"],
        request_body=ResetPasswordSerializer,
        responses={
            200: "Password reset successfully",
            400: "Invalid data",
        },
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password reset successfully"}, status=status.HTTP_200_OK
        )


class ResendOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Resend OTP",
        tags=["Password Recovery"],
        request_body=ResendOtpSerializer,
        responses={
            200: "OTP sent to email",
            400: "Too many requests / Invalid email",
        },
    )
    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)
