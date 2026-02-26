#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
VENV_DIR="$REPO_ROOT/.venv"

prompt_and_wait() {
    local message="$1"

    echo ""
    echo "$message"
    read -r -p "Press Enter after installing to re-check..." _
}

check_python() {
    while true; do
        if ! command -v python >/dev/null 2>&1; then
            prompt_and_wait "Python 3.10+ is required but was not found in PATH."
            continue
        fi

        if python - <<'PY'
import sys
major, minor = sys.version_info[:2]
sys.exit(0 if (major, minor) >= (3, 10) else 1)
PY
        then
            break
        fi

        prompt_and_wait "Python 3.10+ is required. Your current Python is too old."
    done
}

check_git() {
    while true; do
        if command -v git >/dev/null 2>&1; then
            git --version >/dev/null 2>&1
            break
        fi

        prompt_and_wait "Git is required but was not found in PATH."
    done
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

check_python
check_git
if [[ ! -f "$REPO_ROOT/.env" ]]; then
    if [[ -f "$REPO_ROOT/.env-template" ]]; then
        cp "$REPO_ROOT/.env-template" "$REPO_ROOT/.env"
        echo "Created .env from .env-template."
    else
        echo "No .env found and .env-template is missing. Please create .env manually."
    fi
fi

read -r -p "Start the local Postgres container now? [y/N] " run_db_setup
if [[ "$run_db_setup" =~ ^[Yy]$ ]]; then
    if [[ -f "$SCRIPT_DIR/db-setup.sh" ]]; then
        bash "$SCRIPT_DIR/db-setup.sh"
    else
        echo "db-setup.sh not found at $SCRIPT_DIR/db-setup.sh"
        exit 1
    fi
fi

# Create virtual environment if it does not exist
if [[ ! -d "$VENV_DIR" ]]; then
    python -m venv "$VENV_DIR"
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    source "$VENV_DIR/Scripts/activate"
else
    source "$VENV_DIR/bin/activate"
fi

# Upgrade pip and install uv (dependency manager)
python -m pip install --upgrade pip
python -m pip install --upgrade uv

# Sync all backend dependencies using uv workspace config
cd "$REPO_ROOT"
uv sync --all-packages

echo "Backend virtual environment and dependencies are ready."
echo "To activate the environment, run: source .venv/Scripts/activate (Windows) or source .venv/bin/activate (Unix)"
