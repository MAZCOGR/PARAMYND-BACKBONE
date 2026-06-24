import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenants.services.cloud_build import list_recent_builds
from tenants.services.sync_service import sync_builds_and_commits
from tenants.models import CloudBuildRecord

print("Initial sync...")
sync_builds_and_commits()

for b in CloudBuildRecord.objects.filter(status='WORKING'):
    print(f"Build {b.build_id} is WORKING, progress: {b.progress}%")

print("Sleeping 5 seconds...")
time.sleep(5)

print("Second sync...")
has_changes = sync_builds_and_commits()
print(f"has_changes = {has_changes}")

for b in CloudBuildRecord.objects.filter(status='WORKING'):
    print(f"Build {b.build_id} is WORKING, progress: {b.progress}%")
