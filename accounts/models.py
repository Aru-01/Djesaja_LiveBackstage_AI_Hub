from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.db import models
from accounts.custom_managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("SUPER_ADMIN", "Super Admin"),
        ("MANAGER", "Manager"),
        ("CREATOR", "Creator"),
    ]

    username = models.CharField(max_length=250, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    profile_image = models.ImageField(upload_to="profiles/", null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
