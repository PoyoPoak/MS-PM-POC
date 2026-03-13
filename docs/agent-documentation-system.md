# Agent Documentation System

## Purpose

This file defines where agent-facing knowledge belongs so documentation stays discoverable, non-duplicated, and easy to maintain.

See [README.md](README.md) for the full documentation index.

## Canonical Layers

| Layer | Primary Location | Use For | Update Frequency |
|---|---|---|---|
| Product and architecture truth | `docs/` | Domain rules, API workflows, model behavior, operations guides | When behavior changes |
| Always-on repo policy | `.github/copilot-instructions.md` | Global conventions, guardrails, required protocols | Low |
| Scoped implementation guidance | `.github/instructions/*.instructions.md` | File/area-specific coding and doc-sync rules | Medium |
| Repeatable task workflows | `.github/skills/*/SKILL.md` | Multi-step procedures agents should follow | Medium |
| One-off task templates | `.github/prompts/*.prompt.md` | Parameterized ad hoc tasks | As needed |
| Durable short facts | `/memories/repo/*.md` | Stable repo facts and pitfalls | Low |

## Single Source Rules

1. Store durable project truth in `docs/` and link to it from other layers.
2. Keep instructions and skills procedural; avoid duplicating long domain explanations.
3. Use repository memory only for short, high-signal facts.
4. Use Git history and pull request descriptions for change history; do not maintain long-running agent changelog files.

## Change-to-Documentation Matrix

| Change Type | Required Update |
|---|---|
| Backend API route changes (`backend/app/api/**`) | Update affected `docs/*.md`; regenerate API client if contract changed |
| Data model/schema changes (`backend/app/models.py`, migrations) | Update `docs/project.md` and affected feature docs |
| ML training/evaluation behavior changes | Update `docs/ml-engine.md` and/or `docs/training_loop.md` |
| Agent workflow/policy changes | Update `.github/instructions/` or `.github/skills/` and this file if architecture rules changed |

## Documentation Contract

A change is not done until one of the following is true:

- Relevant docs/instructions were updated in the same pull request.
- The pull request explicitly states why no documentation update is required.

## CI Enforcement

Documentation sync is enforced by workflow `documentation-sync.yml`, which runs `.github/scripts/check-doc-sync.sh`.

Current checks:

- API and model changes require at least one docs update.
- Agent-instruction and skill changes require this architecture file to be updated.

## Migration Playbook (From Ad Hoc Notes)

1. Collect existing agent update notes.
2. Classify each note as policy, workflow, domain truth, or temporary context.
3. Move policy to instructions, workflow to skills, domain truth to docs.
4. Remove temporary notes after the corresponding pull request is merged.
5. Keep only this architecture file as the meta index for the system.
