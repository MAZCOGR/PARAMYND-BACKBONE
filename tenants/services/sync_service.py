"""
tenants/services/sync_service.py
Service pour synchroniser les données Git et Cloud Build avec la base de données.
"""
import logging
from tenants.models import GitCommitRecord, CloudBuildRecord
from tenants.services import git_service, cloud_build

logger = logging.getLogger(__name__)

def sync_builds_and_commits() -> bool:
    """
    Récupère les données depuis les API et les synchronise avec la BDD.
    Retourne True si de nouvelles données ont été ajoutées ou modifiées, False sinon.
    """
    has_changes = False

    try:
        # 1. Sync Git Commits (Backbone)
        recent_commits = git_service.get_recent_commits(limit=10)
        db_hashes = set(GitCommitRecord.objects.values_list('hash', flat=True))
        api_hashes = set(c['hash'] for c in recent_commits)
        
        if db_hashes != api_hashes:
            is_mock = any(c['author'] == 'Alex' for c in recent_commits)
            if not is_mock or len(db_hashes) == 0:
                has_changes = True
                GitCommitRecord.objects.all().delete()
                # Insert oldest first so newest gets highest fetched_at
                for commit in reversed(recent_commits):
                    GitCommitRecord.objects.create(
                        hash=commit['hash'],
                        short_hash=commit['short_hash'],
                        message=commit['message'],
                        author=commit['author'],
                        date_str=commit['date'],
                        commit_date_iso=commit.get('commit_date_iso'),
                        branch=commit['branch'],
                        tag=commit.get('tag')
                    )

        # 1.5 Sync Git Commits (SaaS)
        from tenants.models import SaaSGitCommitRecord
        saas_recent_commits = git_service.get_saas_commits(limit=10)
        saas_db_hashes = set(SaaSGitCommitRecord.objects.values_list('hash', flat=True))
        saas_api_hashes = set(c['hash'] for c in saas_recent_commits)
        
        # Don't overwrite real data with mock data if we already have real data
        is_saas_mock = any(c['author'] == 'Alex' for c in saas_recent_commits)
        if saas_db_hashes != saas_api_hashes:
            if not is_saas_mock or len(saas_db_hashes) == 0:
                has_changes = True
                SaaSGitCommitRecord.objects.all().delete()
                # Insert oldest first so newest gets highest fetched_at
                for commit in reversed(saas_recent_commits):
                    SaaSGitCommitRecord.objects.create(
                        hash=commit['hash'],
                        short_hash=commit['short_hash'],
                        message=commit['message'],
                        author=commit['author'],
                        date_str=commit['date'],
                        commit_date_iso=commit.get('commit_date_iso'),
                        branch=commit['branch'],
                        tag=commit.get('tag')
                    )

        # 2. Sync Cloud Builds
        recent_builds = cloud_build.list_recent_builds(limit=10)
        db_builds = {b.build_id: b.status for b in CloudBuildRecord.objects.all()}
        api_builds = {b['id']: b['status'] for b in recent_builds}
        
        # Don't overwrite real data with mock data if we already have real data
        is_builds_mock = any(b['id'].startswith('build-') for b in recent_builds)
        if db_builds != api_builds:
            if not is_builds_mock or len(db_builds) == 0:
                has_changes = True
                CloudBuildRecord.objects.all().delete()
                for build in recent_builds:
                    CloudBuildRecord.objects.create(
                        build_id=build['id'],
                        status=build['status'],
                        created_str=build['created'],
                        duration=build['duration'],
                        commit_sha=build['commit_sha'],
                        branch_name=build['branch_name'],
                        tags=build['tags'],
                        images=build.get('images', [])
                    )

    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation : {e}")

    return has_changes
