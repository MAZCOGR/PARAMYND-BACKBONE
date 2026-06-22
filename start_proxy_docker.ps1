# ==============================================================================
# start_proxy_docker.ps1 - Cloud SQL Proxy pour Docker (ecoute sur 0.0.0.0)
# A utiliser a la place de start_proxy.ps1 quand Django tourne dans Docker
# Ouvrir dans un terminal SEPARE et laisser tourner
# ==============================================================================

$INSTANCE       = "yellow-455523:europe-west9:yellow-db-paris"
$PROXY_PORT     = 5433
$PROXY_EXE      = "C:\yellow_backend_V4\yellow_backend\cloud-sql-proxy.exe"
$SA_KEY         = "C:\yellow_backend_V4\yellow_backend\service-account-key.json"

Write-Host ""
Write-Host "[Paramynd Admin] - Cloud SQL Proxy (mode Docker)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host "  Instance : $INSTANCE" -ForegroundColor Gray
Write-Host "  Ecoute   : 0.0.0.0:$PROXY_PORT  <- accessible depuis Docker" -ForegroundColor Green
Write-Host "  Base     : paramynd_admin" -ForegroundColor Gray
Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host ""

# 0.0.0.0 = ecoute sur toutes les interfaces, y compris celle visible par Docker
& $PROXY_EXE $INSTANCE --address 0.0.0.0 --port $PROXY_PORT --credentials-file $SA_KEY
