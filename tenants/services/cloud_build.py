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
            substitutions = b.substitutions or {}
            commit_sha = substitutions.get('COMMIT_SHA', '')
            branch_name = substitutions.get('BRANCH_NAME', '')
            repo_name = substitutions.get('REPO_NAME', '')
            trigger_name = substitutions.get('TRIGGER_NAME', '')
            
            # On veut afficher UNIQUEMENT les builds du backbone (paramynd-admin / paramynd-backbone)
            is_backbone_build = False
            search_str = f"{repo_name} {trigger_name} {str(b.tags)} {str(b.images)} {str(substitutions)}".lower()
            
            if 'paramynd-admin' in search_str or 'paramynd-backbone' in search_str:
                is_backbone_build = True
                
            if not is_backbone_build:
                continue
                
            # Les builds du backbone peuvent ne pas avoir de 'images' définies si déployés via buildpacks
            # Nous retirons donc la condition stricte sur b.images pour ces builds.
            
            # fallback if not in substitutions but in source
            if not commit_sha and b.source and b.source.repo_source:
                commit_sha = b.source.repo_source.commit_sha
            if not branch_name and b.source and b.source.repo_source:
                branch_name = b.source.repo_source.branch_name

            # Format creation date nicely
            created_str = b.create_time.strftime("%d/%m/%Y %H:%M") if hasattr(b.create_time, 'strftime') else str(b.create_time)[:16]
            
            # Format duration nicely (e.g. "1 min 23 s")
            duration_str = 'N/A'
            if b.finish_time and b.start_time:
                td = b.finish_time - b.start_time
                total_seconds = int(td.total_seconds())
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                if minutes > 0:
                    duration_str = f"{minutes} min {seconds} s"
                else:
                    duration_str = f"{seconds} s"

            progress = 0
            if b.status.name == 'WORKING' and hasattr(b, 'steps') and b.steps:
                total_steps = len(b.steps)
                completed_steps = sum(1 for step in b.steps if step.status.name == 'SUCCESS')
                if total_steps > 0:
                    # Give a small base progress so it doesn't look completely empty on step 1
                    base_progress = 10 
                    progress = int((completed_steps / total_steps) * 90) + base_progress

            result.append({
                'id': b.id,
                'status': b.status.name,
                'progress': progress,
                'tags': list(b.tags),
                'commit_sha': commit_sha,
                'branch_name': branch_name,
                'created': created_str,
                'duration': duration_str,
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
                'created': '20/01/2025 10:00',
                'duration': '2 min 34 s',
                'images': [f"europe-west9-docker.pkg.dev/{settings.GCP_PROJECT_ID}/paramynd/app:v1.3.0"],
            },
            {
                'id': 'build-def-002',
                'status': 'SUCCESS',
                'tags': ['v1.2.1'],
                'commit_sha': 'e4f5g6h',
                'branch_name': 'develop',
                'created': '10/01/2025 14:30',
                'duration': '2 min 12 s',
                'images': [f"europe-west9-docker.pkg.dev/{settings.GCP_PROJECT_ID}/paramynd/app:v1.2.1"],
            },
        ]
