# Copilot Coding Agent Instructions

Trust these instructions first. Only search the codebase if information here is incomplete or found to be in error.

## Repository Overview

**Pacemaker Telemetry Risk Monitoring Platform** — an interview-showcase MLOps web application built on the FastAPI Full Stack Template. The project demonstrates end-to-end software engineering: synthetic pacemaker telemetry generation, ML training/evaluation (Random Forest), model registry, risk predictions, email alerting, and a React dashboard — all orchestrated with CI/CD. **This is not a template — it is a real application.** Make changes as application features, not template improvements. See `docs/project.md` for the full specification and `docs/pacemaker-telemetry.md` for telemetry feature definitions.

- **Backend**: Python 3.10+ · FastAPI · SQLModel ORM · PostgreSQL · Alembic migrations · JWT auth
- **Frontend**: React 19 · TypeScript · Vite · Tailwind CSS 4 · shadcn/ui · TanStack Router/Query
- **ML**: scikit-learn Random Forest · OOB & K-Fold evaluation · model versioning/registry
- **Package managers**: `uv` (Python) · `bun` (JavaScript/TypeScript) — **NEVER use pip/poetry/npm/yarn**
- **Infrastructure**: Docker Compose · Traefik reverse proxy · Mailcatcher (dev email)
- **Linting**: Ruff + mypy (backend) · Biome (frontend) · prek pre-commit hooks
- **Testing**: pytest (backend, ≥90% coverage required) · Playwright (frontend E2E)

## Project Layout

```
.                            # Root: workspace configs, Docker Compose, .env
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entrypoint
│   │   ├── models.py        # SQLModel data models (User, Item + future telemetry/ML models)
│   │   ├── crud.py          # Database CRUD operations
│   │   ├── core/
│   │   │   ├── config.py    # Pydantic Settings (reads ../.env)
│   │   │   ├── db.py        # Database engine & init
│   │   │   └── security.py  # JWT & password hashing
│   │   ├── api/
│   │   │   ├── main.py      # API router aggregation (all routes under /api/v1)
│   │   │   ├── deps.py      # Dependency injection (auth, DB session)
│   │   │   └── routes/      # Endpoint modules: items, users, login, utils, private
│   │   ├── alembic/         # Migration scripts (versions/ dir)
│   │   └── email-templates/ # MJML source (src/) and built HTML (build/)
│   ├── tests/               # pytest tests (conftest.py, api/, crud/, utils/, scripts/)
│   ├── scripts/             # prestart.sh, tests-start.sh, test.sh, lint.sh, format.sh
│   ├── pyproject.toml       # Python deps + ruff/mypy/coverage config
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── main.tsx         # React entrypoint
│   │   ├── client/          # Auto-generated OpenAPI SDK (DO NOT edit)
│   │   ├── components/      # App components + ui/ (shadcn — DO NOT edit ui/)
│   │   ├── routes/          # TanStack Router file-based pages
│   │   └── hooks/           # Custom React hooks (useAuth, etc.)
│   ├── tests/               # Playwright E2E tests
│   ├── package.json         # Scripts: dev, build, lint, generate-client, test
│   ├── biome.json           # Biome linter/formatter config
│   ├── openapi-ts.config.ts # OpenAPI client codegen config
│   └── components.json      # shadcn/ui configuration
├── docs/                    # project.md (spec), pacemaker-telemetry.md (features), deployment.md, development.md
├── scripts/                 # generate-client.sh, test.sh, test-local.sh
├── .env                     # Environment variables (shared by backend & Docker Compose, never commit secrets)
├── .env-template            # Template for CI — workflows copy this and inject secrets
├── compose.yml              # Production Docker Compose
├── compose.override.yml     # Dev overrides (ports, hot-reload, mailcatcher, playwright)
├── pyproject.toml           # Root uv workspace (members: ["backend"])
├── package.json             # Root bun workspace (workspaces: ["frontend"])
└── .pre-commit-config.yaml  # prek hooks config
```

## Build, Test & Lint Commands (Validated)

All commands run from the **repository root** unless noted. The backend requires a running PostgreSQL. Always run the steps in the order shown.

### Bootstrap (always run first after clone or dependency change)
```bash
uv sync --all-packages          # Python deps — MUST run from repo root
bun install                     # Frontend deps — MUST run from repo root
```

### Backend (requires Docker for DB)
```bash
docker compose up -d db mailcatcher                      # Start database + mail
cd backend && uv run bash scripts/prestart.sh && cd ..   # Migrations + seed (REQUIRED before tests)
cd backend && uv run bash scripts/tests-start.sh && cd ..# Tests + coverage report (60 tests, ~4s)
cd backend && uv run coverage report --fail-under=90 && cd .. # Verify ≥90% coverage
```

### Backend Lint & Format
```bash
cd backend && uv run bash scripts/lint.sh && cd ..       # mypy + ruff check + ruff format --check
cd backend && uv run bash scripts/format.sh && cd ..     # Auto-fix: ruff check --fix + ruff format
# Ruff only (used by pre-commit):
uv run ruff check --force-exclude --fix
uv run ruff format --force-exclude
```

### Frontend
```bash
bun run lint                     # Biome check + auto-fix (from repo root)
cd frontend && bun run build && cd ..  # TypeScript check + Vite build
```

### Regenerate Frontend OpenAPI Client (ALWAYS after backend API/model changes)
```bash
bash ./scripts/generate-client.sh   # Extracts OpenAPI JSON → openapi-ts → bun lint
# Commit the resulting changes in frontend/src/client/
```

### Full Stack Docker
```bash
docker compose up -d db mailcatcher backend frontend   # Start services
docker compose down -v --remove-orphans                # Clean teardown
```

### Alembic Migrations (when modifying SQLModel table classes)
1. Modify models in `backend/app/models.py`.
2. Ensure new model modules are imported in `backend/app/alembic/env.py` (existing `app.models` import covers that file).
3. `docker compose exec backend alembic revision --autogenerate -m "description"` (or `cd backend && uv run alembic revision --autogenerate -m "description"` if running locally with DB up).
4. Verify the generated file in `backend/app/alembic/versions/` has real SQL in `upgrade()`.
5. `docker compose exec backend alembic upgrade head` (or `cd backend && uv run alembic upgrade head`).

## CI Checks (All Must Pass for PR Merge)

| Workflow | File | What it checks |
|---|---|---|
| **pre-commit** | `.github/workflows/pre-commit.yml` | prek hooks: ruff, biome, YAML/TOML, whitespace, end-of-file, SDK regeneration. Auto-commits fixes. |
| **Test Backend** | `.github/workflows/test-backend.yml` | PostgreSQL + mailcatcher → prestart.sh → tests-start.sh → coverage ≥90%. Python 3.10. |
| **Playwright** | `.github/workflows/playwright.yml` | Docker build → Playwright E2E sharded 4 ways. Triggers on backend/, frontend/, .env, compose*.yml changes. |
| **Test Docker Compose** | `.github/workflows/test-docker-compose.yml` | Build + start full stack → curl health endpoints (`/api/v1/utils/health-check` and frontend). |
| **Markdown Links** | `.github/workflows/markdown-links.yml` | Validates all local file links in .md files resolve to existing files. |
| **Smokeshow** | `.github/workflows/smokeshow.yml` | Publishes coverage report after Test Backend completes. |
| **Latest Changes** | `.github/workflows/latest-changes.yml` | Auto-updates release-notes.md on merged PRs. |

CI .env handling: workflows copy `.env-template` and inject secrets — never commit a real `.env`.

## Cross-Stack Dependency Protocol

If you modify `backend/app/api/`, `backend/app/models.py`, or any backend route/schema:
1. Restart the backend dev server (or let hot-reload pick up changes).
2. Run `bash ./scripts/generate-client.sh` to regenerate `frontend/src/client/`.
3. **Commit** the regenerated files in `frontend/src/client/`.
4. Fix any resulting TypeScript errors in `frontend/src/`.

## Documentation Sync Protocol

When implementation changes are made, update documentation in the same work item when appropriate.

- **Class/major function/component changes**: update or create the corresponding instruction file in `.github/instructions/` when behavior, inputs/outputs, contracts, or usage expectations change.
- **Feature/workflow/API/data model changes**: update impacted docs under `docs/` (for example `docs/project.md`, `docs/pacemaker-telemetry.md`, `docs/development.md`, `docs/ml-engine.md`).
- **Definition of done**: do not treat implementation-only changes as complete until relevant `.github/instructions` and/or `docs` updates are included.
- **Avoid doc drift**: if no documentation update is needed, explicitly verify that existing `.github/instructions` and `docs` content remains accurate for the change.

## Key Conventions

- **Python**: Target 3.10. Ruff rules: pycodestyle, pyflakes, isort, flake8-bugbear, comprehensions, pyupgrade, `T201` (no `print()`), `ARG001` (no unused args). `B904` ignored (HTTPException).
- **TypeScript**: Biome — double quotes, space indent, semicolons as-needed. Auto-generated files excluded: `src/client/`, `src/components/ui/`, `src/routeTree.gen.ts`.
- **DO NOT manually edit**: `frontend/src/client/**`, `frontend/src/components/ui/**`, `frontend/src/routeTree.gen.ts`.
- **Environment variables**: All in root `.env`. Backend reads via pydantic-settings from `../.env`. Never commit real secrets.
- **API prefix**: All routes under `/api/v1`. The `private` router loads only when `ENVIRONMENT=local`.
- **Shell scripts**: Must use LF line endings (`.gitattributes` enforces `*.sh text eol=lf`).
- **Coverage**: Backend ≥90% or CI fails.
- **NEVER** use `pip`, `poetry`, `npm`, or `yarn`. **NEVER** edit `uv.lock` or `bun.lock` manually.

## Common Pitfalls

- **Backend tests need PostgreSQL running**: Always `docker compose up -d db mailcatcher` and run `prestart.sh` before pytest.
- **Frontend client out of sync**: Changing backend API and forgetting `bash ./scripts/generate-client.sh` will fail pre-commit and CI.
- **`uv sync --all-packages`** must run from repo root for workspace resolution. `uv sync` from `backend/` works for backend-only deps.
- **`bun install`** must run from repo root. Root `bun.lock` is source of truth.
- **mypy strict mode**: `backend/pyproject.toml` sets `strict = true`. Ensure all new Python code has proper type annotations.

## Agent Skills

This project has **loaded agent skills** that provide domain-specific instructions for common tasks. **Always read the relevant SKILL.md before implementing** when the task matches a skill domain.

### Repo-local skills (`.github/skills/`)

| Skill | Trigger | File |
|---|---|---|
| `backend-testing` | Writing pytest tests, adding coverage, creating fixtures, fixing test failures | `.github/skills/backend-testing/SKILL.md` |
| `create-endpoint` | Adding new API routes, CRUD resources, full-stack vertical slices | `.github/skills/create-endpoint/SKILL.md` |
| `database-migration` | Modifying schemas, adding/removing columns, creating tables, changing SQLModel fields | `.github/skills/database-migration/SKILL.md` |
| `frontend-component` | Creating React components, pages, forms, data tables, dialogs | `.github/skills/frontend-component/SKILL.md` |

### General capability skills (`.agents/skills/`)

| Skill | Trigger |
|---|---|
| `api-design-principles` | API shape, REST design, naming, versioning |
| `frontend-design` | Design/style/beautify frontend UI |
| `ml-pipeline-workflow` | End-to-end ML/MLOps pipeline design and automation |
| `mermaid-diagrams` | Diagram/visualize architecture, flows, schemas |
| `refactor` | Clean up/restructure code without behavior change |
| `crafting-effective-readmes` | README authoring/improvement |
| `find-skills` | Discover/install new skills |
| `skill-creator` | Create, modify, or evaluate skills |

**Invocation rule**: Read the `SKILL.md` file first, then follow its instructions. Prioritize repo-local skills (more specific) over general skills.

## Playwright E2E Protocol

- **Write tests with semantic locators only**: `page.getByRole('button', { name: 'Submit' })` — never CSS selectors.
- **Auth**: Use the setup project in `frontend/tests/auth.setup.ts` and storage state at `playwright/.auth/user.json`. Don't script login flows unless the test is about login.
- **Healing**: If a test fails, assume the UI changed. Analyze the HTML dump and update the locator.
