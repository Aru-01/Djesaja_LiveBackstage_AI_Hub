from django.core.cache import cache
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from accounts.models import User
from accounts.utils import (
    generate_otp,
    set_otp_cache,
    send_otp_email,
    get_otp_cache,
    delete_otp_cache,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name",
            "email",
            "profile_image",
            "role",
            "email_verified",
        ]
        read_only_fields = ["id"]


class SelfProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "username", "profile_image"]

    def validate_username(self, value):
        user = self.context["request"].user
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["username"] = user.username
        token["email"] = user.email
        token["role"] = getattr(user, "role", None)
        token["email_verified"] = getattr(user, "email_verified", False)

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": getattr(self.user, "role", None),
            "email_verified": getattr(self.user, "email_verified", False),
        }

        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password incorrect")
        return value

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User not found")
        return value

    def save(self):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)
        otp = generate_otp()
        set_otp_cache(f"forgot_{user.id}", otp)
        send_otp_email(email, otp, "forgot_password")


class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

    def validate(self, data):
        user = User.objects.get(email=data["email"])
        cached_otp = get_otp_cache(f"forgot_{user.id}")
        if not cached_otp:
            raise serializers.ValidationError("OTP expired")
        if cached_otp != data["otp"]:
            raise serializers.ValidationError("Invalid OTP")
        return data

    def save(self):
        user = User.objects.get(email=self.validated_data["email"])
        cache.set(f"forgot_verified_{user.id}", True, timeout=600)
        delete_otp_cache(f"forgot_{user.id}")


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        user = User.objects.get(email=data["email"])
        verified = cache.get(f"forgot_verified_{user.id}")
        if not verified:
            raise serializers.ValidationError("OTP not verified or expired")
        return data

    def save(self):
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["new_password"])
        user.save()
        cache.delete(f"forgot_verified_{user.id}")
        return user


class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["forgot_password", "verify_email"])

    def validate(self, data):
        if not User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError("User not found")
        return data

    def save(self):
        email = self.validated_data["email"]
        purpose = self.validated_data["purpose"]
        user = User.objects.get(email=email)

        cooldown_key = f"{purpose}_resend_{user.id}"
        if cache.get(cooldown_key):
            raise serializers.ValidationError(
                "OTP recently sent. Wait 30s before resending."
            )

        otp = generate_otp()

        if purpose == "forgot_password":
            set_otp_cache(f"forgot_{user.id}", otp)
        else:
            set_otp_cache(user.id, otp)

        send_otp_email(email, otp, purpose)
        cache.set(cooldown_key, True, timeout=30)
