"""
accounts/backends.py — Backend d'authentification par email
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """Authentification par email au lieu du username."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        # Bug #1 fix : guard explicite sur email=None.
        # Sans ce guard, User.objects.get(email__iexact=None) lève une ValueError
        # (pas un DoesNotExist) qui n'est pas catchée → 500 en production.
        if not email:
            return None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        # H-05 fix : vérifier is_active — un user désactivé ne garde pas sa session
        try:
            user = User.objects.get(pk=user_id)
            return user if self.user_can_authenticate(user) else None
        except User.DoesNotExist:
            return None
