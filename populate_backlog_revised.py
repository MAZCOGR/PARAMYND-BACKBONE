import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import Project, Sprint, Task

def run():
    # Find the existing SaaS project
    project = Project.objects.filter(name__icontains="saas").first()
    if not project:
        print("Error: No existing project with 'saas' in its name found.")
        return

    print(f"Found project: '{project.name}'. Resetting all sprints and tasks...")

    # Delete existing sprints (cascade deletes tasks)
    Sprint.objects.filter(project=project).delete()
    print("Existing sprints and tasks deleted.")

    # Full revised backlog (26-week robust B2B SaaS plan)
    backlog_data = [
        {
            "sprint_name": "Sprint 1 : Fondations GCP + IaC + Sécurité",
            "tasks": [
                "Configurer le projet GCP (IAM, Réseau VPC, Pare-feu).",
                "Écrire les scripts Terraform pour provisioner l'infrastructure (AlloyDB, Redis, Pub/Sub).",
                "Configurer Google Secret Manager pour toutes les clés API et credentials.",
                "Créer les 3 environnements GCP : dev, staging, prod.",
                "Configurer les pipelines CI/CD Cloud Build séparés pour chaque environnement.",
                "Initialiser le projet Frontend (Next.js 14+) avec TypeScript.",
                "Initialiser le projet Backend (Python / FastAPI) avec structure modulaire.",
            ]
        },
        {
            "sprint_name": "Sprint 2 : Schéma DB + Migrations + Multi-Tenancy",
            "tasks": [
                "Décider et documenter la stratégie Multi-Tenancy (partagée avec tenant_id ou une DB par client).",
                "Configurer Alembic (Python) pour la gestion des migrations de schéma AlloyDB.",
                "Créer le schéma de base : Tenants, Users, Workspaces, Roles.",
                "Créer le schéma dimensionnel : Dimensions, Lists, Modules, Cells.",
                "Implémenter le Row-Level Security (RLS) AlloyDB dès le départ.",
                "Créer les tests unitaires de validation d'isolation des Tenants.",
            ]
        },
        {
            "sprint_name": "Sprint 3 : Data Grid + Virtualisation + Audit Log",
            "tasks": [
                "Intégrer AG Grid (Enterprise) dans Next.js avec TypeScript.",
                "Implémenter la virtualisation des lignes et colonnes (chargement à la demande).",
                "Développer l'API Backend paginée pour requêter les données de la grille.",
                "Implémenter le serveur WebSockets sur Cloud Run.",
                "Gérer la concurrence : Optimistic Locking sur les cellules.",
                "Implémenter l'Audit Log : chaque modification de cellule est tracée (who, what, when).",
                "Connecter l'édition de cellule UI à l'API avec feedback visuel de sauvegarde.",
            ]
        },
        {
            "sprint_name": "Sprint A : Moteur de Formules (Parser + AST)",
            "tasks": [
                "Décider la stratégie du moteur de formules : AI-Native (LLM interprète) vs Parser classique.",
                "Définir la syntaxe du langage de formule (ex: SUM, AVG, IF, LOOKUP, PREVIOUS).",
                "Développer le parser d'expressions (AST - Arbre Syntaxique Abstrait) en Python.",
                "Implémenter les fonctions de base : SUM, AVERAGE, IF, MIN, MAX.",
                "Implémenter les fonctions dimensionnelles : LOOKUP, FILTER par dimension.",
                "Implémenter la détection des références circulaires dans le graphe.",
                "Développer le moteur d'erreur (division par zéro, ref invalide, etc.).",
                "Tests unitaires exhaustifs du parser et de chaque fonction.",
            ]
        },
        {
            "sprint_name": "Sprint 4 : Moteur de Calcul DAG + Temps Réel",
            "tasks": [
                "Développer le Graphe Orienté Acyclique (DAG) des dépendances de formules.",
                "Connecter le parser du Sprint A au moteur DAG.",
                "Implémenter la stratégie de persistance du DAG dans Redis (survie aux redémarrages Cloud Run).",
                "Implémenter la reconstruction rapide du DAG depuis AlloyDB au démarrage.",
                "Connecter le Backend à Cloud Pub/Sub pour écouter les événements de modification.",
                "Implémenter le cycle complet E2E : UI -> API -> Pub/Sub -> DAG -> AlloyDB -> WS -> UI.",
                "Tests de régression : vérifier qu'un changement de cellule ne propage pas d'erreurs en cascade.",
            ]
        },
        {
            "sprint_name": "Sprint B : Gestion des Accès RBAC",
            "tasks": [
                "Définir le modèle RBAC complet : Admin, Modeler, Analyst, Viewer.",
                "Implémenter les guards d'API côté FastAPI (décorateurs de permission).",
                "Implémenter les restrictions visuelles côté Next.js (composants conditionnels).",
                "Implémenter les droits au niveau Workspace, Modèle et Module.",
                "Intégrer l'authentification : Google Identity / Firebase Auth.",
                "Implémenter le SSO (SAML 2.0 / OIDC) pour les clients Enterprise.",
                "Tests d'intégration de l'isolation des droits entre Tenants.",
            ]
        },
        {
            "sprint_name": "Sprint 5 : Agent IA d'Ingestion (Auto-ETL)",
            "tasks": [
                "Configurer l'accès à Vertex AI (Gemini 1.5 Pro) depuis Cloud Run.",
                "Créer l'interface Frontend d'upload de fichiers Smart Import (CSV, Excel).",
                "Développer l'Agent LangChain d'analyse sémantique (mapping automatique des colonnes).",
                "Implémenter la génération de schéma AlloyDB et l'insertion des données nettoyées.",
                "Interface de validation Human-in-the-loop : l'utilisateur valide le mapping avant insertion.",
                "Implémenter la vue 'Rapport d'erreurs d'import' pour les lignes rejetées.",
                "Implémenter l'idempotence : détecter et rejeter les fichiers déjà importés (hash).",
            ]
        },
        {
            "sprint_name": "Sprint 6 : Agent de Modélisation (Text-to-Schema)",
            "tasks": [
                "Intégrer l'interface Chat / Copilot persistante dans Next.js (barre latérale).",
                "Développer l'Agent de Modélisation avec Prompt Engineering avancé (Gemini).",
                "Connecter l'Agent à l'API pour créer dynamiquement des dimensions et modules.",
                "Afficher visuellement le résultat de la création du modèle dans la Data Grid.",
                "Implémenter la commande 'Annuler' (Undo) sur la création de modèle par IA.",
            ]
        },
        {
            "sprint_name": "Sprint C : Gestion des Scénarios & Versions",
            "tasks": [
                "Concevoir le modèle de données pour les Scénarios (Snapshot d'un modèle à un instant T).",
                "Créer l'interface UI de création et nommage de scénarios.",
                "Implémenter la duplication d'un modèle en nouveau scénario.",
                "Développer la vue comparaison côte-à-côte de 2 scénarios.",
                "Implémenter le versioning (historique des snapshots avec dates).",
                "Permettre l'export d'un scénario en Excel/CSV.",
            ]
        },
        {
            "sprint_name": "Sprint 7 : Reporting & Generative UI",
            "tasks": [
                "Développer l'Agent Analyste (Text-to-SQL optimisé AlloyDB).",
                "Configurer l'Agent pour réponses JSON structurées (type + data).",
                "Implémenter les composants Generative UI dans Next.js (graphiques Recharts/Tremor).",
                "Implémenter les droits sur les rapports (RLS dans la couche UI).",
                "Sauvegarde des requêtes : épingler un graphique dans un Dashboard persistant.",
                "Implémenter le scheduling de rapports (envoi automatique par email).",
                "Implémenter l'export de rapports en PDF.",
            ]
        },
        {
            "sprint_name": "Sprint D : Billing & Gestion des Abonnements",
            "tasks": [
                "Définir les tiers d'abonnement (Starter, Pro, Enterprise) et leurs limites.",
                "Intégrer Stripe pour la gestion des paiements et abonnements.",
                "Implémenter les Webhooks Stripe pour activer/désactiver les features par plan.",
                "Créer le Portail d'abonnement pour les Tenants (upgrade, factures, annulation).",
                "Implémenter les quotas : limite de modèles, de lignes, d'utilisateurs par plan.",
                "Implémenter les alertes de dépassement de quotas.",
            ]
        },
        {
            "sprint_name": "Sprint 8 : Sécurité Avancée + RGPD + PRA",
            "tasks": [
                "Activer le chiffrement CMEK (Customer Managed Encryption Keys) sur AlloyDB.",
                "Rédiger et implémenter la politique de rétention des données (RGPD).",
                "Implémenter le droit à l'oubli (suppression des données d'un Tenant).",
                "Configurer les sauvegardes automatiques AlloyDB avec RPO et RTO définis.",
                "Configurer le Plan de Reprise d'Activité (PRA) Multi-Région GCP.",
                "Réaliser un audit de sécurité (Penetration Testing) avant lancement.",
                "Documenter le DPA (Data Processing Agreement) pour les clients EU.",
            ]
        },
        {
            "sprint_name": "Sprint 9 : Tests de Charge, Beta & Lancement",
            "tasks": [
                "Tests de charge sur Cloud Run et AlloyDB (simuler 100 users simultanés).",
                "Tests E2E automatisés sur les scénarios critiques (Playwright).",
                "Onboarding de 3 à 5 clients Beta pour tests en conditions réelles.",
                "Refonte UX/UI finale (design system Paramynd, micro-animations, feedbacks IA).",
                "Mise en place du monitoring complet (Cloud Logging, Trace, Alerting).",
                "Déploiement en production (environnement prod) avec rollout progressif.",
                "Documentation utilisateur et aide contextuelle dans l'application.",
            ]
        },
    ]

    for sprint_data in backlog_data:
        sprint = Sprint.objects.create(
            name=sprint_data["sprint_name"],
            project=project
        )
        print(f"  + Sprint: {sprint.name}")
        for task_title in sprint_data["tasks"]:
            Task.objects.create(
                title=task_title[:200],
                project=project,
                sprint=sprint,
                status='TODO'
            )
        print(f"    -> {len(sprint_data['tasks'])} tasks created.")

    print(f"\nRevised backlog successfully attached to project '{project.name}'!")
    print(f"Total sprints: {len(backlog_data)}")
    total_tasks = sum(len(s['tasks']) for s in backlog_data)
    print(f"Total tasks: {total_tasks}")

if __name__ == '__main__':
    run()
