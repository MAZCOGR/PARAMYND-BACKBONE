# ==============================================================================
# start_all.ps1
# Lancement global pour l'environnement de developpement Docker
# ==============================================================================

Write-Host ""
Write-Host "DEMARRAGE DE L'ENVIRONNEMENT LOCAL" -ForegroundColor Magenta
Write-Host "------------------------------------" -ForegroundColor DarkGray

# 1. Demarrer le proxy Cloud SQL dans une nouvelle fenetre
Write-Host "1. Lancement du Proxy Cloud SQL dans une nouvelle fenetre..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\paramynd-admin; .\start_proxy_docker.ps1" -WindowStyle Normal

# Attendre que le proxy demarre
Start-Sleep -Seconds 4

# 2. Demarrer Paramynd Admin (Backbone)
Write-Host "2. Demarrage de Paramynd Admin (port 8002)..." -ForegroundColor Cyan
Set-Location -Path "c:\paramynd-admin"
docker compose down
docker compose up -d --build

# 3. Demarrer Paramynd (Client SaaS)
Write-Host "3. Demarrage de Paramynd (port 8001)..." -ForegroundColor Cyan
Set-Location -Path "c:\paramynd"
docker compose down
docker compose up -d --build

Write-Host ""
Write-Host "TOUT EST PRET !" -ForegroundColor Green
Write-Host "  Backbone (Admin) : http://localhost:8002" -ForegroundColor White
Write-Host "  Paramynd (Client): http://localhost:8001/auth/login/" -ForegroundColor White
Write-Host "------------------------------------" -ForegroundColor DarkGray
Write-Host ""
