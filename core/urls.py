from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render

from .views import home_view, building_workspace_view, request_demo_view, verify_otp_view

urlpatterns = [
    path('', home_view, name='home'),
    path('building-workspace/', building_workspace_view, name='building_workspace'),
    path('request-demo/', request_demo_view, name='request_demo'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('auth/', include('accounts.urls', namespace='accounts')),
    path('tenants/', include('tenants.urls', namespace='tenants')),
    path('monitoring/', include('monitoring.urls', namespace='monitoring')),
    path('admin/', admin.site.urls),

    # API REST
    path('api/auth/', include('accounts.api_urls', namespace='api_accounts')),
    path('api/v1/tenants/', include('tenants.api_urls', namespace='api_tenants')),

    # OAuth2
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
