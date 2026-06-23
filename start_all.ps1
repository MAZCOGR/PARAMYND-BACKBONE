# ==============================================================================
# start_all.ps1
# Lancement global pour l'environnement de développement Docker
# ==============================================================================

Write-Host ""
Write-Host "🚀 DÉMARRAGE DE L'ENVIRONNEMENT LOCAL (SSO)" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

# 1. Démarrer le proxy Cloud SQL dans une nouvelle fenêtre
Write-Host "1. Lancement du Proxy Cloud SQL dans une nouvelle fenêtre..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\paramynd-admin; .\start_proxy_docker.ps1" -WindowStyle Normal

# Attendre un peu que le proxy démarre
Start-Sleep -Seconds 3

# 2. Démarrer Paramynd Admin (Backbone)
Write-Host "2. Démarrage de Paramynd Admin (Backbone sur port 8002)..." -ForegroundColor Cyan
Set-Location -Path "c:\paramynd-admin"
docker-compose down
docker-compose up -d --build

# 3. Démarrer Paramynd (Client SaaS)
Write-Host "3. Démarrage de Paramynd (Client sur port 8001)..." -ForegroundColor Cyan
Set-Location -Path "c:\paramynd"
docker-compose down
docker-compose up -d --build

Write-Host ""
Write-Host "✅ TOUT EST PRÊT !" -ForegroundColor Green
Write-Host "  👉 Backbone (Admin) : http://localhost:8002" -ForegroundColor White
Write-Host "  👉 Paramynd (Client) : http://localhost:8001/auth/login/" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
