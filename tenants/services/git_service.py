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

def get_recent_commits(limit: int = 10) -> List[Dict]:
    """
    Exécute `git log` sur le dossier local partagé et retourne les commits.
    """
    try:
        # Format : hash|message|auteur|date|branches
        command = [
            "git", "-C", REPO_PATH, "log", f"-n{limit}",
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
                branch_display = branch_list[0] if branch_list else ''
                # Remove HEAD -> etc
                if '->' in branch_display:
                    branch_display = branch_display.split('->')[-1].strip()

                try:
                    # ISO 8601 parsing
                    dt = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    formatted_date = date[:16]

                commits.append({
                    'hash': commit_hash,
                    'short_hash': commit_hash[:8],
                    'message': message,
                    'author': author,
                    'date': formatted_date,
                    'branch': branch_display,
                })
        
        if not commits:
            raise ValueError("Aucun commit trouvé")
            
        return commits
        
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
