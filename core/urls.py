from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render

def home_view(request):
    """Landing page publique de Paramynd Admin."""
    return render(request, 'home.html')


urlpatterns = [
    path('', home_view, name='home'),
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
