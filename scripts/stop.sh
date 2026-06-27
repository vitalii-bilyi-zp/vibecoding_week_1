#!/usr/bin/env bash
# Stop and remove the app container (Mac/Linux).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
docker compose -f "$root/docker-compose.yml" down
echo "App stopped"
