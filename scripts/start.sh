#!/usr/bin/env bash
# Build and start the app container (Mac/Linux).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
docker compose -f "$root/docker-compose.yml" up --build -d
echo "App running at http://localhost:8000"
