"""
Script de mise à jour en masse des tâches terminées du Sprint 1.
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import Task

updates = [
    {
        "fragment": "Initialiser le projet Frontend (Next.js)",
        "status": "DONE",
        "note": "N/A — Non applicable. Architecture choisie : Django Server-Side Rendering + AG Grid + Channels. Pas de Next.js séparé pour rester dans l'écosystème Django existant."
    },
    {
        "fragment": "Initialiser le projet Backend (Python/FastAPI)",
        "status": "DONE",
        "note": "N/A — Non applicable. Backend déjà existant en Django 5.0 + DRF. FastAPI remplacé par Django Rest Framework déjà en place. Uvicorn ajouté pour ASGI."
    },
    {
        "fragment": "Définir le schéma de base de donn",
        "status": "TESTED",
        "note": "✅ FAIT — App Django 'planning' créée avec modèles complets : Workspace (multi-tenant), Dimension, DimensionItem, Module, Scenario, Cell (avec formule AI), AuditLog. Migration générée. Fichier : c:/paramynd/planning/models.py"
    },
    {
        "fragment": "Créer le schéma DB pour les Modèles Dimensionnels",
        "status": "TESTED",
        "note": "✅ FAIT — Modèles dimensionnels créés : Dimension (avec hiérarchie parent/enfant), DimensionItem, Module (multi-dimensions), Cell (coordonnées JSON + formule AI). Migration générée. Fichier : c:/paramynd/planning/models.py"
    },
    {
        "fragment": "Implémenter le serveur WebSockets",
        "status": "TESTED",
        "note": "✅ FAIT — Django Channels installé (channels==4.1.0, channels-redis==4.2.0). ASGI configuré dans core/asgi.py. ProtocolTypeRouter configuré. CHANNEL_LAYERS Redis configuré dans settings.py. Dockerfile mis à jour : Gunicorn → Uvicorn ASGI."
    },
]

for update in updates:
    tasks = Task.objects.filter(title__icontains=update["fragment"])
    count = tasks.count()
    if count == 0:
        print(f"[WARN] Aucune tache trouvee : '{update['fragment']}'")
        continue
    for task in tasks:
        task.status = update["status"]
        task.notes = update["note"]
        task.save()
        print(f"[OK] [{update['status']}] {task.title}")

print("\nMise a jour terminee !")
