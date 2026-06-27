from django.urls import path
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

app_name = 'api_accounts'


class LoginRateThrottle(AnonRateThrottle):
    """
    Bug #10 fix : rate limiting dédié pour le endpoint de login JWT côté Admin.
    Limite : 10 tentatives/minute par IP (protection brute-force).
    Identique au LoginRateThrottle de paramynd/accounts/api_urls.py.
    """
    scope = 'login_attempt'


class ThrottledTokenObtainPairView(views.ParamyndTokenObtainPairView):
    """Vue JWT avec throttling anti-brute-force appliqué."""
    throttle_classes = [LoginRateThrottle]


urlpatterns = [
    # JWT — throttled (Bug #10 fix)
    path('token/', ThrottledTokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('me/', views.me_view, name='me'),
    path('logout/', views.logout_api_view, name='logout'),
]
