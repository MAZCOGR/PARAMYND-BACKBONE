"""
Utilitaire pour mettre à jour le statut et les notes d'une tâche dans le gestionnaire de projet.
Usage: python update_task.py "titre partiel de la tache" TESTED "note de ce qui a été fait"
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import Task

def update_task(title_fragment, status, note):
    tasks = Task.objects.filter(title__icontains=title_fragment)
    if not tasks.exists():
        print(f"❌ Aucune tâche trouvée contenant : '{title_fragment}'")
        return
    for task in tasks:
        task.status = status
        task.notes = note
        task.save()
        print(f"✅ Tâche mise à jour : [{status}] {task.title}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python update_task.py '<titre>' <STATUS> '<note>'")
        sys.exit(1)
    update_task(sys.argv[1], sys.argv[2], sys.argv[3])
