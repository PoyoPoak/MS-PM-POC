#!/bin/bash
set -euo pipefail

UPSTREAM_URL="https://github.com/fastapi/full-stack-fastapi-template"
UPSTREAM_COMMIT="d40de23"

prompt_and_wait() {
    local message="$1"

    echo ""
    echo "$message"
    read -r -p "Press Enter to continue..." _
}

check_git() {
    if ! command -v git >/dev/null 2>&1; then
        echo "Git is required but was not found in PATH."
        exit 1
    fi
}

check_repo() {
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "This script must be run inside a git repository."
        exit 1
    fi
}

ensure_upstream_remote() {
    if git remote get-url upstream >/dev/null 2>&1; then
        git remote set-url upstream "$UPSTREAM_URL"
    else
        git remote add upstream "$UPSTREAM_URL"
    fi
}

verify_upstream_commit() {
    if ! git cat-file -e "$UPSTREAM_COMMIT"^{commit} >/dev/null 2>&1; then
        echo "Fetching upstream to locate commit $UPSTREAM_COMMIT..."
        git fetch upstream --tags --prune
    fi

    if ! git cat-file -e "$UPSTREAM_COMMIT"^{commit} >/dev/null 2>&1; then
        echo "Commit $UPSTREAM_COMMIT was not found after fetching upstream."
        exit 1
    fi
}

check_base_commit() {
    if git merge-base --is-ancestor "$UPSTREAM_COMMIT" HEAD; then
        echo "OK: current HEAD is based on upstream commit $UPSTREAM_COMMIT."
        return
    fi

    echo "WARNING: current HEAD is NOT based on upstream commit $UPSTREAM_COMMIT."
    echo "To base this repo on that commit, you can reset or rebase manually."
    prompt_and_wait "Review your branch state and proceed with manual steps if needed."
}

check_git
check_repo
ensure_upstream_remote
verify_upstream_commit
check_base_commit

echo "Upstream remote set to $UPSTREAM_URL."
