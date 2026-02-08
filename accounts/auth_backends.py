from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from accounts.models import User


class UsernameEmailUIDBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            user = User.objects.get(
                Q(username=username) | Q(email=username) | Q(uid=username)
            )
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
