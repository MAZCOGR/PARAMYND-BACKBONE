"""
tenants/services/git_service.py
Récupérer l'historique Git du projet Paramynd.

- Backbone (admin) : git log local (même conteneur, toujours à jour)
- SaaS (client)    : GitHub API (le clone local est figé au build Docker,
                     git fetch désactivé car bloque sans credentials Cloud Run)
"""
import logging
import subprocess
import datetime
import time
from typing import List, Dict

from django.conf import settings

logger = logging.getLogger(__name__)

REPO_PATH = str(settings.BASE_DIR)

# ── GitHub API pour le repo SaaS (toujours à jour) ───────────────────────────
GITHUB_ORG  = getattr(settings, 'GITHUB_ORG',  'MAZCOGR')
GITHUB_REPO = getattr(settings, 'GITHUB_REPO', 'PARAMYND')

# Cache en mémoire : évite de dépasser la limite GitHub (60 req/h sans token, 5000 avec)
_saas_cache: Dict = {'data': [], 'fetched_at': 0}
CACHE_TTL = 60  # secondes


def get_saas_commits(limit: int = 50) -> List[Dict]:
    """
    Récupère les commits du repo SaaS via l'API GitHub.
    Utilise un cache mémoire de 60s pour ne pas dépasser le rate limit.
    Supporte la pagination pour récupérer plus de 100 commits.
    Fallback sur git log local si l'API est indisponible.
    """
    global _saas_cache
    now = time.time()

    # Retourner le cache si encore frais
    if _saas_cache['data'] and (now - _saas_cache['fetched_at']) < CACHE_TTL:
        return _saas_cache['data'][:limit]

    try:
        import requests
        token = getattr(settings, 'GITHUB_TOKEN', None)
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if token:
            headers['Authorization'] = f'token {token}'

        commits = []
        page = 1
        per_page = min(limit, 100)  # GitHub API max per_page = 100

        while len(commits) < limit:
            url = (
                f'https://api.github.com/repos/{GITHUB_ORG}/{GITHUB_REPO}/commits'
                f'?per_page={per_page}&page={page}'
            )
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()

            page_data = resp.json()
            if not page_data:
                break  # Plus de commits disponibles

            for item in page_data:
                sha    = item['sha']
                msg    = item['commit']['message'].split('\n')[0]  # première ligne seulement
                author = item['commit']['author']['name']
                date_str = item['commit']['author']['date']  # ISO 8601

                try:
                    dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date  = dt.strftime('%d/%m/%Y %H:%M')
                    commit_date_iso = dt.isoformat()
                except ValueError:
                    formatted_date  = date_str[:16]
                    commit_date_iso = None

                commits.append({
                    'hash':            sha,
                    'short_hash':      sha[:7],
                    'message':         msg,
                    'author':          author,
                    'date':            formatted_date,
                    'commit_date_iso': commit_date_iso,
                    'branch':          'origin/main',
                    'tag':             '',
                })

            if len(page_data) < per_page:
                break  # Dernière page atteinte

            page += 1

        _saas_cache = {'data': commits, 'fetched_at': now}
        return commits[:limit]

    except Exception as e:
        logger.warning(f'GitHub API indisponible ({e}) — fallback git log local')
        # Fallback : git log sur le clone local (peut être obsolète)
        import os
        local_path = '/app/paramynd_repo' if os.path.exists('/app/paramynd_repo') else r'c:\paramynd'
        return _get_commits_from_repo(local_path, limit)


def get_recent_commits(limit: int = 10) -> List[Dict]:
    """
    Exécute `git log` sur le dossier local partagé (backbone) et retourne les commits.
    """
    return _get_commits_from_repo(REPO_PATH, limit)


def _get_commits_from_repo(repo_path: str, limit: int = 10) -> List[Dict]:
    try:
        # Removed `git fetch` because it hangs without credentials in Cloud Run

        # Format : hash|message|auteur|date|branches
        command = [
            "git", "-c", "safe.directory=*", "-C", repo_path, "log", f"-n{limit}",
            "--pretty=format:%H|%s|%an|%cd|%D", "--date=iso-strict"
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 4)
            if len(parts) == 5:
                commit_hash, message, author, date, branches = parts

                branch_list = [b.strip() for b in branches.split(',') if b.strip()]
                tag_display = next(
                    (b.replace('tag:', '').strip() for b in branch_list if b.startswith('tag:')), ''
                )
                branch_display = next(
                    (b for b in branch_list
                     if not b.startswith('tag:') and b != 'HEAD' and not b.startswith('HEAD ->')),
                    branch_list[0] if branch_list else ''
                )

                if '->' in branch_display:
                    branch_display = branch_display.split('->')[-1].strip()

                commit_date_iso = None
                try:
                    dt = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date  = dt.strftime("%d/%m/%Y %H:%M")
                    commit_date_iso = dt.isoformat()
                except ValueError:
                    formatted_date = date[:16]

                commits.append({
                    'hash':            commit_hash,
                    'short_hash':      commit_hash[:7],
                    'message':         message,
                    'author':          author,
                    'date':            formatted_date,
                    'commit_date_iso': commit_date_iso,
                    'branch':          branch_display,
                    'tag':             tag_display,
                })

        if not commits:
            raise ValueError("Aucun commit trouvé")

        return commits

    except subprocess.CalledProcessError as e:
        logger.warning(f"Git log error: {e.stderr} — retour des données mock")
    except Exception as e:
        logger.warning(f"Git log non disponible ({e}) — retour des données mock")

    return [
        {
            'hash': 'a1b2c3d4e5f6g7h8i9j0',
            'short_hash': 'a1b2c3d',
            'message': 'feat: initialisation du projet',
            'author': 'Alex',
            'date': '23/06/2026 10:00',
            'commit_date_iso': None,
            'branch': 'main',
            'tag': '',
        },
        {
            'hash': 'b2c3d4e5f6g7h8i9j0a1',
            'short_hash': 'b2c3d4e',
            'message': 'fix: correction du bug css',
            'author': 'Alex',
            'date': '22/06/2026 14:30',
            'commit_date_iso': None,
            'branch': '',
            'tag': '',
        },
    ]
