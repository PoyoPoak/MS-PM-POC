#!/usr/bin/env bash
set -euo pipefail

BASE_SHA="${BASE_SHA:-}"
HEAD_SHA="${HEAD_SHA:-}"

if [[ -z "$BASE_SHA" || -z "$HEAD_SHA" ]]; then
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    BASE_SHA="$(git merge-base origin/main HEAD)"
    HEAD_SHA="HEAD"
  else
    BASE_SHA="HEAD~1"
    HEAD_SHA="HEAD"
  fi
fi

echo "Checking documentation sync between $BASE_SHA and $HEAD_SHA"

CHANGED_FILES="$(git diff --name-only "$BASE_SHA" "$HEAD_SHA")"

echo "Changed files:"
echo "$CHANGED_FILES"

if [[ -z "$CHANGED_FILES" ]]; then
  echo "No changed files detected."
  exit 0
fi

has_change() {
  local pattern="$1"
  echo "$CHANGED_FILES" | grep -Eq "$pattern"
}

has_docs_update() {
  has_change '^docs/.*\.md$'
}

# Rule 1: API and model changes require docs updates.
if has_change '^backend/app/api/.*\.py$|^backend/app/models\.py$'; then
  if ! has_docs_update; then
    echo "ERROR: Backend API/model changes detected without docs updates under docs/*.md"
    exit 1
  fi
fi

# Rule 2: Agent customization changes require architecture map update.
if has_change '^\.github/instructions/.*\.md$|^\.github/skills/.*/SKILL\.md$|^\.github/copilot-instructions\.md$'; then
  if ! has_change '^docs/agent-documentation-system\.md$'; then
    echo "ERROR: Agent instruction/skill policy changed without updating docs/agent-documentation-system.md"
    exit 1
  fi
fi

echo "Documentation sync checks passed."
