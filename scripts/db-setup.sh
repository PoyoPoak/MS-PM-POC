#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

prompt_and_wait() {
    local message="$1"

    echo ""
    echo "$message"
    read -r -p "Press Enter after installing to re-check..." _
}

check_docker() {
    while true; do
        if ! command -v docker >/dev/null 2>&1; then
            prompt_and_wait "Docker Desktop is required but was not found in PATH."
            continue
        fi

        if docker --version >/dev/null 2>&1; then
            break
        fi

        prompt_and_wait "Docker is required but does not appear to be working."
    done
}

check_docker_compose() {
    while true; do
        if docker compose version >/dev/null 2>&1; then
            break
        fi

        prompt_and_wait "Docker Compose (via Docker Desktop) is required but was not found."
    done
}

check_docker
check_docker_compose

if [[ ! -f "$REPO_ROOT/.env" ]]; then
    if [[ -f "$REPO_ROOT/.env-template" ]]; then
        cp "$REPO_ROOT/.env-template" "$REPO_ROOT/.env"
        echo "Created .env from .env-template."
    else
        echo "No .env found and .env-template is missing. Please create .env manually."
        exit 1
    fi
fi

cd "$REPO_ROOT"
docker compose up -d db

echo "Postgres container is starting."
