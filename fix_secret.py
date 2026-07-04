import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from oauth2_provider.models import Application
from django.contrib.auth.hashers import make_password

app = Application.objects.get(client_id='uxmskgX5Qq5DQn15FxelHQPmN34Im4JTZ1frhpXz')
print("Current secret:", app.client_secret)
# Django OAuth Toolkit handles hashing automatically if OAUTH2_PROVIDER['HASH_CLIENT_SECRETS'] = True
# Usually we should just set it to plain text, but if the save method doesn't hash it properly (or we bypassed it)
app.client_secret = 'paramynd_super_secret_key_123'
app.save()
print("Updated secret.")
