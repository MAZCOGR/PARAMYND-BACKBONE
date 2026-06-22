"""
accounts/serializers.py — Serializers DRF pour l'API auth
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class ParamyndTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT token avec champs supplémentaires."""
    username_field = 'email'

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.get_full_name()
        return token

    def validate(self, attrs):
        # Renommer 'username' en 'email' pour le backend
        attrs['email'] = attrs.get(self.username_field)
        return super().validate(attrs)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
