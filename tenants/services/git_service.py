"""
tenants/services/git_service.py
Récupérer l'historique Git du projet Paramynd.
"""
import logging
import subprocess
import datetime
from typing import List, Dict

from django.conf import settings

logger = logging.getLogger(__name__)

REPO_PATH = str(settings.BASE_DIR)

import os
# Si on est dans Docker, le volume est monté sur /app/paramynd_repo
if os.path.exists('/app/paramynd_repo'):
    SAAS_REPO_PATH = '/app/paramynd_repo'
else:
    SAAS_REPO_PATH = r"c:\paramynd"

def get_saas_commits(limit: int = 10) -> List[Dict]:
    """
    Exécute `git log` sur le dossier du SaaS et retourne les commits.
    """
    return _get_commits_from_repo(SAAS_REPO_PATH, limit)

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
                
                # Format branch string
                branch_list = [b.strip() for b in branches.split(',') if b.strip()]
                
                tag_display = next((b.replace('tag:', '').strip() for b in branch_list if b.startswith('tag:')), '')
                branch_display = next((b for b in branch_list if not b.startswith('tag:') and b != 'HEAD' and not b.startswith('HEAD ->')), branch_list[0] if branch_list else '')
                
                if '->' in branch_display:
                    branch_display = branch_display.split('->')[-1].strip()

                commit_date_iso = None
                try:
                    # ISO 8601 parsing
                    dt = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%d/%m/%Y %H:%M")
                    commit_date_iso = dt.isoformat()
                except ValueError:
                    formatted_date = date[:16]

                commits.append({
                    'hash': commit_hash,
                    'short_hash': commit_hash[:7],
                    'message': message,
                    'author': author,
                    'date': formatted_date,
                    'commit_date_iso': commit_date_iso,
                    'branch': branch_display,
                    'tag': tag_display,
                })
        
        if not commits:
            raise ValueError("Aucun commit trouvé")
            
        return commits
        
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git log error 128: {e.stderr} - retour des données mock")
        return [
            {
                'hash': 'a1b2c3d4e5f6g7h8i9j0',
                'short_hash': 'a1b2c3d4',
                'message': 'feat: initialisation du projet',
                'author': 'Alex',
                'date': '23/06/2026 10:00',
                'branch': 'main',
            },
            {
                'hash': 'b2c3d4e5f6g7h8i9j0a1',
                'short_hash': 'b2c3d4e5',
                'message': 'fix: correction du bug css',
                'author': 'Alex',
                'date': '22/06/2026 14:30',
                'branch': '',
            },
        ]
    except Exception as e:
        logger.warning(f"Git log non disponible ({e}) — retour des données mock")
        return [
            {
                'hash': 'a1b2c3d4e5f6g7h8i9j0',
                'short_hash': 'a1b2c3d4',
                'message': 'feat: initialisation du projet',
                'author': 'Alex',
                'date': '23/06/2026 10:00',
                'branch': 'main',
            },
            {
                'hash': 'b2c3d4e5f6g7h8i9j0a1',
                'short_hash': 'b2c3d4e5',
                'message': 'fix: correction du bug css',
                'author': 'Alex',
                'date': '22/06/2026 14:30',
                'branch': '',
            },
        ]
