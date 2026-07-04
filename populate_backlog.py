import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import Project, Sprint, Task

def run():
    # 1. RESET: Delete existing project to start fresh
    existing_projects = Project.objects.filter(name__icontains="paramynd saas")
    if existing_projects.exists():
        print(f"Deleting existing project(s) to reset...")
        existing_projects.delete()
        
    project_name = "Paramynd SaaS"
    project = Project.objects.create(name=project_name, description='Paramynd SaaS Platform avec AI Planning')
    print(f"Created clean project: {project.name}")

    # Define sprints and tasks
    backlog_data = [
        {
            "sprint_name": "Sprint 1 : Fondations GCP & Infrastructure",
            "tasks": [
                "Configurer le projet GCP (IAM, Réseau VPC, Sécurité).",
                "Provisionner Google AlloyDB (création du cluster, pgvector).",
                "Provisionner Memorystore (Redis) et topics Cloud Pub/Sub.",
                "Initialiser le projet Frontend (Next.js) et CI/CD sur Cloud Run.",
                "Initialiser le projet Backend (Python/FastAPI) et CI/CD Cloud Run.",
                "Définir le schéma de base de données (Tenants, Users, Workspaces)."
            ]
        },
        {
            "sprint_name": "Sprint 2 : Cœur de Modélisation & Grille de Données",
            "tasks": [
                "Créer le schéma DB pour les Modèles Dimensionnels (Dimensions, Lists, Cells).",
                "Intégrer une Data Grid performante (AG Grid) dans Next.js.",
                "Développer l'API Backend pour la Data Grid.",
                "Implémenter le serveur WebSockets.",
                "Connecter l'édition de cellule UI à l'API."
            ]
        },
        {
            "sprint_name": "Sprint 3 : Le Moteur de Calcul & Temps Réel",
            "tasks": [
                "Développer la logique du DAG (Graphe Orienté Acyclique) en Python.",
                "Connecter le Backend à Pub/Sub pour les événements.",
                "Connecter le moteur à Memorystore (Redis).",
                "Implémenter le cycle complet E2E (UI -> API -> Pub/Sub -> DAG -> AlloyDB -> WS -> UI)."
            ]
        },
        {
            "sprint_name": "Sprint 4 : Agent IA d'Ingestion (Auto-ETL)",
            "tasks": [
                "Configurer l'accès à Vertex AI (Gemini 1.5).",
                "Créer l'interface d'upload de fichiers Smart Import.",
                "Développer l'Agent LangChain d'analyse sémantique.",
                "Développer la génération de schéma AlloyDB et insertion.",
                "Interface de validation de mapping (Human-in-the-loop)."
            ]
        },
        {
            "sprint_name": "Sprint 5 : Agent de Modélisation (Text-to-Schema)",
            "tasks": [
                "Intégrer l'interface Chat / Copilot dans Next.js.",
                "Développer l'Agent de Modélisation (Prompt Engineering).",
                "Connecter l'Agent à l'API du Moteur de Calcul (Text-to-Schema).",
                "Afficher visuellement le résultat dans la Data Grid."
            ]
        },
        {
            "sprint_name": "Sprint 6 : Reporting & Generative UI",
            "tasks": [
                "Développer l'Agent Analyste (Text-to-SQL).",
                "Configurer l'Agent pour réponses JSON structurées.",
                "Implémenter les composants Generative UI (Recharts/Tremor).",
                "Sauvegarde des requêtes et Dashboarding persistant."
            ]
        },
        {
            "sprint_name": "Sprint 7 : Multi-Tenancy, Sécurité & Lancement",
            "tasks": [
                "Vérification du Row-Level Security (RLS) dans AlloyDB.",
                "Intégration de l'authentification.",
                "Refonte UX/UI finale et micro-animations.",
                "Tests de charge Cloud Run et AlloyDB.",
                "Déploiement en production et monitoring."
            ]
        }
    ]

    for sprint_data in backlog_data:
        sprint = Sprint.objects.create(
            name=sprint_data["sprint_name"],
            project=project
        )
        print(f"Created sprint: {sprint.name}")

        for task_title in sprint_data["tasks"]:
            task = Task.objects.create(
                title=task_title[:200],  # Max length 200
                project=project,
                sprint=sprint,
                status='TODO'
            )
            print(f"  - Created task: {task.title}")

    print("Backlog successfully reset and repopulated!")

if __name__ == '__main__':
    run()
