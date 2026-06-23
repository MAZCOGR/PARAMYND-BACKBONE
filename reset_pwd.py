import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(email='admin@paramynd.com')
u.set_password('admin123')
u.save()
print('Password reset to admin123')
