# Stop and remove the app container (Windows).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
docker compose -f "$root\docker-compose.yml" down
Write-Output "App stopped"
