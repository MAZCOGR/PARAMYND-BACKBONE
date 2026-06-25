"""
accounts/views.py — Vues web (login/logout) et API REST
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ParamyndTokenObtainPairSerializer, UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


# ──────────────────────────────────────────────
# VUES WEB (Session Django)
# ──────────────────────────────────────────────

def get_login_redirect_url(user):
    """Détermine l'URL de redirection après connexion."""
    if user.is_staff or user.is_superuser:
        return '/tenants/'
    
    from tenants.models import Tenant
    user_tenants = Tenant.objects.filter(contact_email=user.email)
    
    if user_tenants.count() == 1:
        tenant = user_tenants.first()
        return f"{tenant.app_url}/auth/login/"
    elif user_tenants.count() > 1:
        return '/tenants/choose/'
    else:
        return '/request-demo/'

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Page de connexion — redirige intelligemment."""
    if request.user.is_authenticated:
        return redirect(get_login_redirect_url(request.user))

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            if not user.is_active:
                messages.error(request, "Ce compte est désactivé.")
            else:
                login(request, user)
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(get_login_redirect_url(user))
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'accounts/login.html')


def logout_view(request):
    """Déconnexion et redirection vers login."""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Vous avez été déconnecté.")
    
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('/')


# ──────────────────────────────────────────────
# API REST — JWT
# ──────────────────────────────────────────────

class ParamyndTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/token/ — Obtenir access + refresh tokens."""
    serializer_class = ParamyndTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """GET /api/auth/me/ — Profil de l'utilisateur courant."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api_view(request):
    """POST /api/auth/logout/ — Blacklister le refresh token (invalidation JWT)."""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'detail': 'Déconnecté avec succès.'}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'detail': 'Token invalide.'}, status=status.HTTP_400_BAD_REQUEST)
