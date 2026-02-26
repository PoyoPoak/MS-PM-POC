#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
FRONTEND_DIR="$REPO_ROOT/frontend"

prompt_and_wait() {
    local message="$1"

    echo ""
    echo "$message"
    read -r -p "Press Enter after installing to re-check..." _
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

check_bun() {
    while true; do
        if command -v bun >/dev/null 2>&1; then
            bun --version >/dev/null 2>&1
            break
        fi

        prompt_and_wait "Bun is required for frontend development but was not found in PATH."
    done
}

check_git
check_bun

if [[ ! -d "$FRONTEND_DIR" ]]; then
    echo "Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

cd "$REPO_ROOT"
bun install

echo "Frontend dependencies are ready."
echo "To start the frontend: cd frontend && bun run dev"
