import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from google.cloud.devtools import cloudbuild_v1
from django.conf import settings

client = cloudbuild_v1.CloudBuildClient()
request = cloudbuild_v1.ListBuildsRequest(
    project_id=settings.GCP_PROJECT_ID,
    page_size=5,
)
builds = client.list_builds(request=request)
for b in builds:
    print(f'Build ID: {b.id}, Status: {b.status.name}')
    if hasattr(b, 'steps'):
        print(f'Steps count: {len(b.steps)}')
        for i, s in enumerate(b.steps):
            print(f'  Step {i}: {s.status.name}')
    else:
        print('No steps attribute.')
