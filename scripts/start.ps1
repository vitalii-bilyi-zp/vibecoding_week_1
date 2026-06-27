# Build and start the app container (Windows).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
docker compose -f "$root\docker-compose.yml" up --build -d
Write-Output "App running at http://localhost:8000"
