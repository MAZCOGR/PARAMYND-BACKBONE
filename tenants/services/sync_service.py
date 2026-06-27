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

    Stratégie incrémentale (upsert) :
    - On ne supprime JAMAIS les enregistrements existants.
    - On insère uniquement les commits/builds inconnus (hash absent en DB).
    - Seul les builds peuvent être mis à jour (statut/progression changeants).
    """
    has_changes = False

    try:
        # ── 1. Sync Git Commits (Backbone) ─────────────────────────────────────
        recent_commits = git_service.get_recent_commits(limit=10)
        is_mock = any(c['author'] == 'Alex' for c in recent_commits)

        if not is_mock:
            db_hashes = set(GitCommitRecord.objects.values_list('hash', flat=True))
            new_commits = [c for c in recent_commits if c['hash'] not in db_hashes]

            if new_commits:
                has_changes = True
                # Insérer du plus ancien au plus récent
                for commit in reversed(new_commits):
                    GitCommitRecord.objects.get_or_create(
                        hash=commit['hash'],
                        defaults={
                            'short_hash':      commit['short_hash'],
                            'message':         commit['message'],
                            'author':          commit['author'],
                            'date_str':        commit['date'],
                            'commit_date_iso': commit.get('commit_date_iso'),
                            'branch':          commit['branch'],
                            'tag':             commit.get('tag'),
                        }
                    )

        # ── 1.5 Sync Git Commits (SaaS) ────────────────────────────────────────
        from tenants.models import SaaSGitCommitRecord

        # Augmenter la limite ici pour alimenter la DB progressivement
        saas_recent_commits = git_service.get_saas_commits(limit=50)
        is_saas_mock = any(c['author'] == 'Alex' for c in saas_recent_commits)

        if not is_saas_mock:
            saas_db_hashes = set(SaaSGitCommitRecord.objects.values_list('hash', flat=True))
            new_saas_commits = [c for c in saas_recent_commits if c['hash'] not in saas_db_hashes]

            if new_saas_commits:
                has_changes = True
                # Insérer du plus ancien au plus récent
                for commit in reversed(new_saas_commits):
                    SaaSGitCommitRecord.objects.get_or_create(
                        hash=commit['hash'],
                        defaults={
                            'short_hash':      commit['short_hash'],
                            'message':         commit['message'],
                            'author':          commit['author'],
                            'date_str':        commit['date'],
                            'commit_date_iso': commit.get('commit_date_iso'),
                            'branch':          commit['branch'],
                            'tag':             commit.get('tag'),
                        }
                    )
        elif SaaSGitCommitRecord.objects.count() == 0:
            # DB vide et données mock : on insère quand même pour avoir quelque chose à afficher
            has_changes = True
            for commit in reversed(saas_recent_commits):
                SaaSGitCommitRecord.objects.get_or_create(
                    hash=commit['hash'],
                    defaults={
                        'short_hash':      commit['short_hash'],
                        'message':         commit['message'],
                        'author':          commit['author'],
                        'date_str':        commit['date'],
                        'commit_date_iso': commit.get('commit_date_iso'),
                        'branch':          commit['branch'],
                        'tag':             commit.get('tag'),
                    }
                )

        # ── 2. Sync Cloud Builds ────────────────────────────────────────────────
        recent_builds = cloud_build.list_recent_builds(limit=10)
        is_builds_mock = any(b['id'].startswith('build-') for b in recent_builds)

        if not is_builds_mock:
            api_builds_map = {b['id']: b for b in recent_builds}
            db_builds_map  = {
                b.build_id: (b.status, b.progress)
                for b in CloudBuildRecord.objects.filter(build_id__in=api_builds_map.keys())
            }

            for build_id, build in api_builds_map.items():
                current = db_builds_map.get(build_id)
                new_status   = build['status']
                new_progress = build.get('progress', 0)

                if current is None:
                    # Nouveau build
                    has_changes = True
                    CloudBuildRecord.objects.create(
                        build_id=build_id,
                        status=new_status,
                        progress=new_progress,
                        created_str=build['created'],
                        duration=build['duration'],
                        commit_sha=build['commit_sha'],
                        branch_name=build['branch_name'],
                        tags=build['tags'],
                        images=build.get('images', []),
                    )
                elif current != (new_status, new_progress):
                    # Build existant mis à jour (statut ou progression changée)
                    has_changes = True
                    CloudBuildRecord.objects.filter(build_id=build_id).update(
                        status=new_status,
                        progress=new_progress,
                    )
        elif CloudBuildRecord.objects.count() == 0:
            # DB vide et données mock : on insère quand même
            has_changes = True
            for build in recent_builds:
                CloudBuildRecord.objects.get_or_create(
                    build_id=build['id'],
                    defaults={
                        'status':      build['status'],
                        'progress':    build.get('progress', 0),
                        'created_str': build['created'],
                        'duration':    build['duration'],
                        'commit_sha':  build['commit_sha'],
                        'branch_name': build['branch_name'],
                        'tags':        build['tags'],
                        'images':      build.get('images', []),
                    }
                )

    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation : {e}")

    return has_changes
