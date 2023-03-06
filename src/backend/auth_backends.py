from django.contrib.auth.backends import AllowAllUsersModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthBackend(AllowAllUsersModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return
        try:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user