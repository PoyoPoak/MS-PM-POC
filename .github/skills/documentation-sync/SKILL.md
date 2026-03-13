---
name: documentation-sync
description: Use when implementing features that modify APIs, models, workflows, or agent customization files and documentation must stay synchronized. Helps classify changes and update docs, instructions, and skills without duplication.
---

# Documentation Sync Skill

## Goal

Update the right documentation artifacts with minimal duplication whenever implementation behavior changes.

## When To Use

- API endpoint additions or contract changes
- Data model/schema modifications
- Training or MLOps workflow changes
- Updates to `.github/instructions/`, `.github/skills/`, or `copilot-instructions.md`

## Procedure

1. Classify the change:
   - Domain truth
   - Policy
   - Workflow
   - Temporary context
2. Apply updates by class:
   - Domain truth -> `docs/*.md`
   - Policy -> `.github/copilot-instructions.md` or `.github/instructions/*.instructions.md`
   - Workflow -> `.github/skills/*/SKILL.md`
   - Temporary context -> PR description or session notes only
3. Add cross-links to canonical docs instead of duplicating long explanations.
4. Verify CI documentation checks pass.

## Output Contract

A documentation-sync task is complete only if:

- Relevant docs are updated in the same PR, or a clear no-doc-change rationale exists.
- Changes do not create duplicate competing sources of truth.
- Architecture map `docs/agent-documentation-system.md` remains accurate.
