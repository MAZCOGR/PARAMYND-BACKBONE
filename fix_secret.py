import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from oauth2_provider.models import Application
app = Application.objects.get(name='Paramynd SSO')
print('Old secret:', app.client_secret)
app.client_secret = 'paramynd_super_secret_key_123'
app.save()
print('New secret saved.')
