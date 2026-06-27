"""
deploy.py — Script de déploiement automatisé vers Google Cloud Run
Usage : python deploy.py

NOTE : Ce script déploie l'application backbone paramynd-admin sur Cloud Run.
Il synchronise automatiquement les variables de votre fichier .env vers Secret Manager.
"""

import subprocess
import sys
import time
import os

PROJECT_ID   = "yellow-455523"
REGION       = "europe-west9"
REPO         = "paramynd"
IMAGE        = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/{REPO}/admin:latest"
SERVICE      = "paramynd-admin"
SQL_INSTANCE = f"{PROJECT_ID}:europe-west9:yellow-db-paris"

# Liste des secrets à synchroniser depuis le .env local vers Secret Manager
SECRETS_MAPPING = {
    "SECRET_KEY": "PARAMYND_ADMIN_SECRET_KEY",
    "DB_PASSWORD": "PARAMYND_ADMIN_DB_PASSWORD",
    "DB_NAME": "PARAMYND_ADMIN_DB_NAME",
    "DB_USER": "PARAMYND_ADMIN_DB_USER",
    "ALLOWED_ADMIN_EMAILS": "PARAMYND_ADMIN_ALLOWED_EMAILS",
    "CORS_ALLOWED_ORIGINS": "PARAMYND_ADMIN_CORS_ORIGINS",
    "ALLOWED_HOSTS": "PARAMYND_ADMIN_ALLOWED_HOSTS",
    "DEBUG": "PARAMYND_ADMIN_DEBUG",
    "GITHUB_TOKEN": "PARAMYND_ADMIN_GITHUB_TOKEN",  # requis pour l'API GitHub (5000 req/h au lieu de 60)
}


def run(step_name: str, cmd: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"  {step_name}")
    print(f"{'='*60}")
    print(f"  $ {' '.join(cmd)}\n")
    start = time.time()
    use_shell = sys.platform == "win32"
    result = subprocess.run(cmd, shell=use_shell)
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"\n❌  ÉCHEC ({step_name}) — code {result.returncode}")
        sys.exit(result.returncode)
    print(f"\n✅  {step_name} terminé en {elapsed:.0f}s")


def run_with_input(cmd: list[str], input_data: str) -> None:
    use_shell = sys.platform == "win32"
    result = subprocess.run(cmd, input=input_data.encode('utf-8'), shell=use_shell, capture_output=True)
    if result.returncode != 0:
        print(f"❌ Erreur lors de l'exécution de {' '.join(cmd)} : {result.stderr.decode('utf-8')}")


def sync_secrets():
    print(f"\n{'='*60}")
    print("  0/2 · Synchronisation des secrets avec Secret Manager")
    print(f"{'='*60}")
    
    if not os.path.exists(".env"):
        print("⚠️ Aucun fichier .env trouvé. On utilise les secrets déjà présents dans GCP.")
        return

    # Parse .env
    env_vars = {}
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
                
    # Quelques surcharges forcées pour la production, 
    # même si elles sont différentes dans le .env local
    env_vars["DEBUG"] = "False"
    env_vars["ALLOWED_HOSTS"] = "*"

    for local_key, gcp_secret_name in SECRETS_MAPPING.items():
        if local_key in env_vars:
            secret_value = env_vars[local_key]
            
            # 1. Vérifier si le secret existe, sinon le créer
            check_cmd = ["gcloud", "secrets", "describe", gcp_secret_name, "--project", PROJECT_ID]
            use_shell = sys.platform == "win32"
            res = subprocess.run(check_cmd, shell=use_shell, capture_output=True)
            if res.returncode != 0:
                print(f"Création du secret : {gcp_secret_name}...")
                create_cmd = ["gcloud", "secrets", "create", gcp_secret_name, "--replication-policy=automatic", "--project", PROJECT_ID]
                subprocess.run(create_cmd, shell=use_shell, capture_output=True)
            
            # 2. Ajouter une nouvelle version avec la valeur
            print(f"Mise à jour de la valeur de : {gcp_secret_name}...")
            add_cmd = ["gcloud", "secrets", "versions", "add", gcp_secret_name, "--data-file=-", "--project", PROJECT_ID]
            run_with_input(add_cmd, secret_value)

    print("\n✅  Synchronisation des secrets terminée")


def main():
    print("\n🚀  Déploiement Paramynd Admin (Backbone) → Cloud Run")
    print(f"    Projet  : {PROJECT_ID}")
    print(f"    Service : {SERVICE}")
    print(f"    Région  : {REGION}\n")

    # ── Étape 0 : Synchroniser les secrets ────────────────────────
    sync_secrets()

    # ── Étape 1 : Build & push de l'image Docker ──────────────────
    run(
        "1/2 · Build & push de l'image Docker",
        [
            "gcloud", "builds", "submit",
            "--tag", IMAGE,
            "--project", PROJECT_ID,
        ],
    )

    # ── Étape 2 : Déploiement sur Cloud Run ───────────────────────
    
    # Construire la liste des secrets pour Cloud Run
    secrets_flags = []
    for local_key, gcp_secret_name in SECRETS_MAPPING.items():
        secrets_flags.append(f"{local_key}={gcp_secret_name}:latest")
    
    secrets_arg = ",".join(secrets_flags)

    run(
        "2/2 · Déploiement sur Cloud Run",
        [
            "gcloud", "run", "deploy", SERVICE,
            "--image",            IMAGE,
            "--region",           REGION,
            "--project",          PROJECT_ID,
            "--platform",         "managed",
            "--allow-unauthenticated",
            "--add-cloudsql-instances", SQL_INSTANCE,
            
            # Variables d'environnement basiques non secrètes
            "--set-env-vars",     "DJANGO_SETTINGS_MODULE=core.settings",
            
            # Tous les secrets injectés proprement
            "--set-secrets",      secrets_arg,

            # ── Ressources ──────────────────────────────────────────
            "--memory",           "512Mi",
            "--cpu",              "1",

            # ── Scaling ─────────────────────────────────────────────
            "--min-instances",    "1",
            "--max-instances",    "5",
        ],
    )

    print("\n🎉  Déploiement complet ! Le service est en ligne.")


if __name__ == "__main__":
    main()
