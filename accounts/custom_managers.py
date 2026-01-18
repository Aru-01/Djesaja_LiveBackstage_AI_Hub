from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(
        self, username, email=None, password=None, role="CREATOR", **extra_fields
    ):
        if not username:
            raise ValueError("Username required")
        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, role=role, **extra_fields)
        if password is None:
            password = username
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        if not password:
            raise ValueError("Superuser must have a password")
        user = self.create_user(username, email=email, password=password, role="SUPER_ADMIN", **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

