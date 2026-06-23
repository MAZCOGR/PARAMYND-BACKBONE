"""
tenants/services/cloud_build.py
Historique des builds Cloud Build.
"""
import logging
from typing import List, Dict
from django.conf import settings

logger = logging.getLogger(__name__)


def list_recent_builds(limit: int = 10) -> List[Dict]:
    """
    Liste les builds récents Cloud Build qui ont généré des artifacts (images).
    """
    try:
        from google.cloud.devtools import cloudbuild_v1

        client = cloudbuild_v1.CloudBuildClient()
        request = cloudbuild_v1.ListBuildsRequest(
            project_id=settings.GCP_PROJECT_ID,
            page_size=limit * 3,  # Fetch more to account for filtering
        )
        
        all_builds = client.list_builds(request=request)
        result = []
        
        for b in all_builds:
            # We only care about builds that produce images
            if not b.images and not (b.results and b.results.images):
                continue
                
            substitutions = b.substitutions or {}
            commit_sha = substitutions.get('COMMIT_SHA', '')
            branch_name = substitutions.get('BRANCH_NAME', '')
            repo_name = substitutions.get('REPO_NAME', '')
            trigger_name = substitutions.get('TRIGGER_NAME', '')
            
            # Filter specifically for paramynd-admin (or paramynd-backbone)
            is_admin_build = False
            search_str = f"{repo_name} {trigger_name} {str(b.tags)} {str(b.images)} {str(substitutions)}".lower()
            if 'paramynd-admin' in search_str or 'paramynd-backbone' in search_str:
                is_admin_build = True
                
            if not is_admin_build:
                continue
            
            # fallback if not in substitutions but in source
            if not commit_sha and b.source and b.source.repo_source:
                commit_sha = b.source.repo_source.commit_sha
            if not branch_name and b.source and b.source.repo_source:
                branch_name = b.source.repo_source.branch_name

            result.append({
                'id': b.id,
                'status': b.status.name,
                'tags': list(b.tags),
                'commit_sha': commit_sha,
                'branch_name': branch_name,
                'created': str(b.create_time),
                'duration': str(b.finish_time - b.start_time) if b.finish_time and b.start_time else 'N/A',
                'images': list(b.images),
            })
            
            if len(result) >= limit:
                break
                
        return result
        
    except Exception as e:
        logger.warning(f"Cloud Build non disponible : {e} — retour des données mock")
        return [
            {
                'id': 'build-abc-001',
                'status': 'SUCCESS',
                'tags': ['v1.3.0'],
                'commit_sha': 'a1b2c3d',
                'branch_name': 'main',
                'created': '2025-01-20T10:00:00Z',
                'duration': '0:02:34',
                'images': [f"europe-west9-docker.pkg.dev/{settings.GCP_PROJECT_ID}/paramynd/app:v1.3.0"],
            },
            {
                'id': 'build-def-002',
                'status': 'SUCCESS',
                'tags': ['v1.2.1'],
                'commit_sha': 'e4f5g6h',
                'branch_name': 'develop',
                'created': '2025-01-10T14:30:00Z',
                'duration': '0:02:12',
                'images': [f"europe-west9-docker.pkg.dev/{settings.GCP_PROJECT_ID}/paramynd/app:v1.2.1"],
            },
        ]
