import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from oauth2_provider.models import Application
app = Application.objects.get(name='Paramynd SSO')
app.skip_authorization = True
app.save()
print('skip_authorization set to True.')
