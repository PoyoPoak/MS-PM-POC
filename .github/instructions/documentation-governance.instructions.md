---
description: Documentation governance rules for syncing implementation changes with agent-facing docs and project docs. Use when editing backend API routes, data models, docs, instructions, or skills.
---

# Documentation Governance Instructions

## Intent

Keep agent context clean and reliable by enforcing single-source documentation and synchronous updates.

## Required Behavior

1. When changing API routes or data contracts, update affected docs in `docs/` in the same change set.
2. When changing implementation behavior in a specific area repeatedly, prefer adding/updating a scoped instruction in `.github/instructions/`.
3. When a multi-step workflow is repeated by agents, create or update a skill in `.github/skills/` instead of adding large prose blocks to instructions.
4. Avoid storing long-running change logs in markdown files for agent memory.
5. If no doc change is required, explicitly justify that in the PR summary.

## Source of Truth Ordering

1. `docs/` for project and feature truth.
2. `.github/copilot-instructions.md` for repo-wide policy.
3. `.github/instructions/` for scoped behavior.
4. `.github/skills/` for repeatable workflows.

## Validation Checklist

- Were affected `docs/*.md` files reviewed?
- Were instructions/skills updated only if behavior contracts changed?
- Was duplicate guidance removed or avoided?
- Does the PR description state documentation impact?
