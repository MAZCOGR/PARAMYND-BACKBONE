import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from oauth2_provider.models import Application
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    print('Creating a default superuser...')
    admin_user = User.objects.create_superuser('admin@paramynd.com', 'admin123')

app, created = Application.objects.get_or_create(
    name='Paramynd SSO',
    defaults={
        'user': admin_user,
        'client_type': Application.CLIENT_CONFIDENTIAL,
        'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
        'redirect_uris': 'http://localhost:8001/social-auth/complete/paramynd-admin/',
    }
)

if not created:
    app.redirect_uris = 'http://localhost:8001/social-auth/complete/paramynd-admin/'
    app.save()

print('=== OAUTH2 APP CREDENTIALS ===')
print('SOCIAL_AUTH_PARAMYND_ADMIN_KEY=' + app.client_id)
print('SOCIAL_AUTH_PARAMYND_ADMIN_SECRET=' + app.client_secret)
