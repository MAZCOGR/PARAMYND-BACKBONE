# ==============================================================================
# Paramynd Admin - docker.ps1
# Script de gestion Docker pour le developpement local
# Usage: .\docker.ps1 [up|down|logs|shell|createsuperuser|reset|status]
# ==============================================================================

param(
    [Parameter(Position=0)]
    [string]$Action = "up"
)

$ErrorActionPreference = "Stop"
$ProjectName = "paramynd-admin"

function Write-Header {
    param([string]$Text, [string]$Color = "Cyan")
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor $Color
    Write-Host "  > $Text" -ForegroundColor $Color
    Write-Host "==================================================" -ForegroundColor $Color
    Write-Host ""
}

switch ($Action) {

    "up" {
        Write-Header "Demarrage de Paramynd Admin en local" "Green"
        Write-Host "  -> Build + demarrage des containers..." -ForegroundColor Yellow
        docker compose up --build -d
        Write-Host ""
        Write-Host "  [OK] Paramynd Admin est demarre !" -ForegroundColor Green
        Write-Host ""
        Write-Host "  [URLs disponibles] :" -ForegroundColor Cyan
        Write-Host "     http://localhost:8002/           -> Accueil Admin"
        Write-Host "     http://localhost:8002/auth/login/ -> Connexion"
        Write-Host "     http://localhost:8002/tenants/    -> Gestion des Tenants"
        Write-Host ""
        Write-Host "  [Logs] : .\docker.ps1 logs" -ForegroundColor Gray
    }

    "down" {
        Write-Header "Arret de Paramynd Admin" "Yellow"
        docker compose down
        Write-Host "  [OK] Containers arretes." -ForegroundColor Green
    }

    "logs" {
        Write-Header "Logs en direct" "Cyan"
        docker compose logs -f
    }

    "logs-web" {
        Write-Header "Logs Django (web)" "Cyan"
        docker compose logs -f web
    }

    "shell" {
        Write-Header "Shell Django (bash)" "Magenta"
        docker compose exec web bash
    }

    "django-shell" {
        Write-Header "Django shell interactif" "Magenta"
        docker compose exec web python manage.py shell
    }

    "createsuperuser" {
        Write-Header "Creation d'un superutilisateur" "Yellow"
        docker compose exec web python manage.py createsuperuser
    }

    "migrate" {
        Write-Header "Application des migrations" "Yellow"
        docker compose exec web python manage.py migrate
    }

    "makemigrations" {
        Write-Header "Generation des migrations" "Yellow"
        docker compose exec web python manage.py makemigrations
    }

    "reset" {
        Write-Header "Reset complet (supprime la DB !)" "Red"
        Write-Host "  [WARNING]  Cette action supprime toutes les donnees !" -ForegroundColor Red
        $confirm = Read-Host "  Confirmer ? (oui/non)"
        if ($confirm -eq "oui") {
            docker compose down -v
            docker compose up --build -d
            Write-Host "  [OK] Reset termine." -ForegroundColor Green
        } else {
            Write-Host "  [Annule]." -ForegroundColor Yellow
        }
    }

    "status" {
        Write-Header "Etat des containers" "Cyan"
        docker compose ps
    }

    "build" {
        Write-Header "Build de l'image" "Yellow"
        docker compose build --no-cache
        Write-Host "  [OK] Build termine." -ForegroundColor Green
    }

    default {
        Write-Host ""
        Write-Host "Usage: .\docker.ps1 [action]" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Actions disponibles :" -ForegroundColor White
        Write-Host "  up               -> Demarrer tous les services (build + run)"
        Write-Host "  down             -> Arreter tous les services"
        Write-Host "  logs             -> Voir tous les logs en direct"
        Write-Host "  logs-web         -> Voir les logs Django uniquement"
        Write-Host "  shell            -> Ouvrir un shell bash dans le container web"
        Write-Host "  django-shell     -> Ouvrir le shell Django interactif"
        Write-Host "  createsuperuser  -> Creer un superutilisateur"
        Write-Host "  migrate          -> Appliquer les migrations"
        Write-Host "  makemigrations   -> Generer les migrations"
        Write-Host "  reset            -> Tout supprimer et repartir de zero"
        Write-Host "  status           -> Etat des containers"
        Write-Host "  build            -> Rebuild l'image sans cache"
        Write-Host ""
    }
}
