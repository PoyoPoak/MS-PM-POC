---
name: create-endpoint
description: Full-stack endpoint implementation guide for creating new API routes, CRUD resources, and vertical slice features across FastAPI backend and React frontend. Use when adding new endpoints, REST resources, database models, API routes, or building full-stack features that span backend routes, database tables, and frontend pages.
---

# Create Endpoint Skill

This skill guides you through implementing a complete full-stack endpoint feature, from database model to frontend UI.

## When to Use This Skill

- Adding new REST API endpoints
- Creating CRUD resources
- Building vertical slice features (database → API → frontend)
- Implementing new database-backed functionality

## SQLModel Model Hierarchy Pattern

Follow the established pattern in `backend/app/models.py` (see `Item` models as reference):

1. **{Thing}Base** - Shared properties (validation, constraints)
   - Use `Field()` with `max_length` on all strings
   - Use `min_length` for required strings
   - Example: `title: str = Field(min_length=1, max_length=255)`

2. **{Thing}Create** - Properties for creation via API
   - Inherits from Base
   - Often just `pass` if no additional fields needed

3. **{Thing}Update** - Properties for updates via API
   - Inherits from Base
   - All fields optional: `field: str | None = Field(default=None, ...)`
   - Use `# type: ignore` on redefined fields

4. **{Thing}** (Database table) - SQLModel with `table=True`
   - `id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)`
   - `created_at: datetime | None = Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))`
   - Foreign keys: `Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")`
   - Relationships: `Relationship(back_populates="...", cascade_delete=True)`

5. **{Thing}Public** - Response model for API
   - Includes `id: uuid.UUID`
   - Includes `created_at: datetime | None = None`
   - Never includes sensitive fields (passwords, etc.)

6. **{Thing}sPublic** - List response wrapper
   - `data: list[{Thing}Public]`
   - `count: int`

**Reference**: `backend/app/models.py` lines 70-108 (Item models)

## Backend Route Implementation

### Route Handler Pattern

**CRITICAL**: Use **synchronous** route handlers (`def`, NOT `async def`). This is the established codebase pattern.

**Reference**: `backend/app/api/routes/items.py` - all handlers use `def`

```python
@router.get("/", response_model={Thing}sPublic)
def read_{thing}s(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve {thing}s."""
    # Implementation
```

### Standard CRUD Endpoints

Implement these 5 endpoints for each resource:

1. **GET /** - List all (with pagination)
   - Query params: `skip: int = 0, limit: int = 100`
   - Return `{Thing}sPublic`
   - Filter by `owner_id` for non-superusers

2. **GET /{id}** - Get single by ID
   - Path param: `id: uuid.UUID`
   - Return `{Thing}Public`
   - Check ownership (403 if not owner and not superuser)
   - 404 if not found

3. **POST /** - Create new
   - Request body: `{thing}_in: {Thing}Create`
   - Set `owner_id` from `current_user.id`
   - Return `{Thing}Public`

4. **PUT /{id}** - Update existing
   - Path param: `id: uuid.UUID`
   - Request body: `{thing}_in: {Thing}Update`
   - Use `model_dump(exclude_unset=True)`
   - Return `{Thing}Public`

5. **DELETE /{id}** - Delete
   - Path param: `id: uuid.UUID`
   - Return `Message(message="{Thing} deleted successfully")`

**Reference**: `backend/app/api/routes/items.py`

### Dependency Injection

Use these standard dependencies from `backend/app/api/deps.py`:

- `SessionDep` - Database session (`Annotated[Session, Depends(get_db)]`)
- `CurrentUser` - Authenticated user (`Annotated[User, Depends(get_current_user)]`)

### Router Registration

Add your router to `backend/app/api/main.py`:

```python
from app.api.routes import items, login, private, users, utils, {things}

api_router.include_router({things}.router)
```

**Reference**: `backend/app/api/main.py` lines 3-10

## CRUD Operations (Optional)

If you need reusable CRUD functions, add them to `backend/app/crud.py`:

```python
def create_{thing}(*, session: Session, {thing}_in: {Thing}Create, owner_id: uuid.UUID) -> {Thing}:
    db_{thing} = {Thing}.model_validate({thing}_in, update={"owner_id": owner_id})
    session.add(db_{thing})
    session.commit()
    session.refresh(db_{thing})
    return db_{thing}
```

**Reference**: `backend/app/crud.py` lines 63-68

## Backend Testing

### Test Coverage Requirement

**All new endpoints MUST have test coverage ≥90%** (CI enforces this).

### Required Test Cases

Create `backend/tests/api/routes/test_{things}.py` with these **11 basic test functions**:

1. `test_create_{thing}` - successful creation
2. `test_read_{thing}` - successful single read
3. `test_read_{thing}_not_found` - 404 handling
4. `test_read_{thing}_not_enough_permissions` - 403 handling
5. `test_read_{things}` - list all
6. `test_update_{thing}` - successful update
7. `test_update_{thing}_not_found` - 404 handling
8. `test_update_{thing}_not_enough_permissions` - 403 handling
9. `test_delete_{thing}` - successful deletion
10. `test_delete_{thing}_not_found` - 404 handling
11. `test_delete_{thing}_not_enough_permissions` - 403 handling

### Additional Test Cases (As Needed)

Depending on your resource's features, also consider these test cases:

**Validation Testing (422 errors)**:
- `test_create_{thing}_invalid_data` - Empty/invalid fields, wrong data types
- `test_update_{thing}_invalid_data` - Invalid update payloads

**Unique Constraints (400 errors)**:
- `test_create_{thing}_duplicate` - Attempting to create duplicate when unique constraint exists
- Example: duplicate email, duplicate slug, etc.

**Pagination Testing**:
- `test_read_{things}_with_pagination` - Test skip/limit parameters
- Verify `count` field accuracy, proper result limiting

**Authentication/Authorization (401 errors)**:
- `test_create_{thing}_unauthenticated` - Request without auth token
- `test_read_{things}_unauthenticated` - List access without auth (if protected)

**Note**: Only add tests for features that actually exist in your endpoint. Don't test pagination if your endpoint doesn't support it. See `backend-testing` skill for detailed examples of each pattern.

### Test Pattern

```python
def test_create_{thing}(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"field1": "value1", "field2": "value2"}
    response = client.post(
        f"{settings.API_V1_STR}/{things}/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["field1"] == data["field1"]
    assert "id" in content
```

**Reference**: `backend/tests/api/routes/test_items.py` (complete example)

### Test Utility Pattern

Create `backend/tests/utils/{thing}.py` for test helpers:

```python
def create_random_{thing}(db: Session) -> {Thing}:
    user = create_random_user(db)
    owner_id = user.id
    field1 = random_lower_string()
    {thing}_in = {Thing}Create(field1=field1, ...)
    return crud.create_{thing}(session=db, {thing}_in={thing}_in, owner_id=owner_id)
```

**Reference**: `backend/tests/utils/item.py`

### Key Test Fixtures

Available from `backend/tests/conftest.py`:

- `db` - Database session
- `client` - TestClient instance
- `superuser_token_headers` - Headers with superuser token
- `normal_user_token_headers` - Headers with normal user token

**Reference**: `backend/tests/conftest.py` lines 16-42

## Database Migration

After creating or modifying models in `backend/app/models.py`:

```bash
# Generate migration (run locally via uv, NOT inside Docker)
cd backend && uv run alembic revision --autogenerate -m "Add {thing} table" && cd ..

# CRITICAL: Manually audit the generated migration file
# - Check for rename detection (drop+add should be op.alter_column or op.rename_table)
# - Verify foreign key constraints
# - Verify index creation
# - Ensure downgrade function is correct

# Apply migration (in development)
docker compose exec backend alembic upgrade head
```

**Reference**: `.github/copilot-instructions.md` lines 143-151

## Frontend Client Regeneration

**CRITICAL SYNCHRONIZATION BARRIER**: After backend changes are complete and tested, regenerate the frontend OpenAPI client:

```bash
bash ./scripts/generate-client.sh
```

This script:
1. Extracts OpenAPI spec from backend
2. Writes `frontend/openapi.json`
3. Runs `openapi-ts` to generate `frontend/src/client/`
4. Runs `bun run lint`

**Never proceed with frontend implementation until this completes successfully.**

**Reference**: `scripts/generate-client.sh`, memory: frontend SDK generation

## Frontend Route Implementation

### File-Based Routing Pattern

Create `frontend/src/routes/_layout/{things}.tsx` using TanStack Router's `createFileRoute`:

```typescript
import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense } from "react"

import { {Thing}sService } from "@/client"

function get{Thing}sQueryOptions() {
  return {
    queryFn: () => {Thing}sService.read{Thing}s({ skip: 0, limit: 100 }),
    queryKey: ["{things}"],
  }
}

export const Route = createFileRoute("/_layout/{things}")({
  component: {Thing}s,
  head: () => ({
    meta: [{ title: "{Thing}s - FastAPI Cloud" }],
  }),
})

function {Thing}sTableContent() {
  const { data: {things} } = useSuspenseQuery(get{Thing}sQueryOptions())

  return <DataTable columns={columns} data={{things}.data} />
}

function {Thing}sTable() {
  return (
    <Suspense fallback={<Pending{Thing}s />}>
      <{Thing}sTableContent />
    </Suspense>
  )
}

function {Thing}s() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{Thing}s</h1>
        <Add{Thing} />
      </div>
      <{Thing}sTable />
    </div>
  )
}
```

**Reference**: `frontend/src/routes/_layout/items.tsx`

### Component Organization

Create these components in `frontend/src/components/{Thing}s/`:

- **Add{Thing}.tsx** - Creation dialog/form
- **Edit{Thing}.tsx** - Edit dialog/form
- **Delete{Thing}.tsx** - Delete confirmation dialog
- **columns.tsx** - DataTable column definitions

### Mutation Pattern with Query Invalidation

For create/update/delete operations, use the pattern from `frontend/src/hooks/useAuth.ts`:

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { {Thing}sService } from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const use{Thing}Mutations = () => {
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const createMutation = useMutation({
    mutationFn: (data: {Thing}Create) =>
      {Thing}sService.create{Thing}({ requestBody: data }),
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["{things}"] })
    },
  })

  return { createMutation }
}
```

**Key points**:
- Use `onSettled` (not `onSuccess`) for query invalidation to ensure it runs even if mutation fails
- Use `handleError.bind(showErrorToast)` for consistent error handling

**Reference**: `frontend/src/hooks/useAuth.ts` lines 29-39

### Existing Hooks

Leverage these hooks from `frontend/src/hooks/`:

- `useAuth` - Authentication state and operations
- `useCustomToast` - Toast notifications
- `useCopyToClipboard` - Copy to clipboard functionality
- `useMobile` - Mobile viewport detection

## Auto-Generated Files (DO NOT EDIT)

These files are auto-generated and must NOT be manually edited:

- `frontend/src/client/**` - Generated by openapi-ts
- `frontend/src/components/ui/**` - Managed by shadcn/ui
- `frontend/src/routeTree.gen.ts` - Generated by TanStack Router

**Reference**: `.github/copilot-instructions.md` lines 183, memory: auto-generated files

## Final Verification

### Backend Verification

```bash
# Start database
docker compose up -d db mailcatcher

# Run migrations
cd backend && uv run bash scripts/prestart.sh && cd ..

# Run tests with coverage check
cd backend && uv run bash scripts/tests-start.sh && cd ..
cd backend && uv run coverage report --fail-under=90 && cd ..

# Lint backend
cd backend && uv run bash scripts/lint.sh && cd ..
```

### Frontend Verification

```bash
# Lint frontend
bun run lint

# Build frontend (TypeScript check)
cd frontend && bun run build && cd ..

# Run E2E tests (optional, requires full stack)
docker compose up -d --wait backend
cd frontend && bunx playwright test && cd ..
```

## Common Pitfalls

- **Using `async def` instead of `def`** - Routes must be synchronous in this codebase
- **Forgetting client regeneration** - Always run `bash ./scripts/generate-client.sh` before frontend work
- **Missing test coverage** - All endpoints need ≥90% coverage
- **Not checking ownership** - Always verify `current_user.is_superuser` or `item.owner_id == current_user.id`
- **Missing migrations** - Run `alembic revision --autogenerate` after model changes
- **Editing auto-generated files** - Never manually edit `frontend/src/client/**`, `frontend/src/components/ui/**`
- **Using `print()` in Python** - Ruff rule T201 forbids this; use logging instead

## Summary Checklist

- [ ] Create SQLModel models following the 6-part hierarchy (Base, Create, Update, DB, Public, PublicList)
- [ ] Implement 5 standard CRUD endpoints with synchronous handlers (`def`)
- [ ] Register router in `backend/app/api/main.py`
- [ ] Create 11 test cases in `backend/tests/api/routes/test_{things}.py`
- [ ] Generate and audit Alembic migration
- [ ] **Run `bash ./scripts/generate-client.sh`** (synchronization barrier)
- [ ] Create frontend route file with `createFileRoute` and `useSuspenseQuery`
- [ ] Implement component files (Add, Edit, Delete, columns)
- [ ] Use mutation pattern with `onSettled` query invalidation
- [ ] Run backend tests (≥90% coverage required)
- [ ] Run backend lint (`cd backend && uv run bash scripts/lint.sh`)
- [ ] Run frontend lint (`bun run lint`)
- [ ] Verify TypeScript build (`cd frontend && bun run build`)
