from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

app_name = 'api_accounts'

urlpatterns = [
    path('token/', views.ParamyndTokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('me/', views.me_view, name='me'),
    path('logout/', views.logout_api_view, name='logout'),
]
