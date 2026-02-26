---
name: backend-testing
description: Backend testing guide for writing pytest tests, adding test coverage, creating fixtures, and fixing failing backend tests. Use when writing tests for FastAPI endpoints, CRUD operations, authentication, adding test coverage, creating test fixtures, or debugging failing backend tests with pytest.
---

# Backend Testing Skill

This skill guides you through writing comprehensive backend tests using pytest for this FastAPI application.

## When to Use This Skill

- Writing tests for new API endpoints
- Adding test coverage to meet the ≥90% requirement
- Creating test fixtures for reusable test data
- Fixing failing backend tests
- Testing CRUD operations
- Testing authentication and authorization
- Debugging test failures

## Test Coverage Requirement

**All backend code MUST maintain ≥90% test coverage** - CI will fail otherwise.

```bash
# Check coverage after running tests
cd backend && uv run coverage report --fail-under=90 && cd ..
```

**Reference**: `.github/copilot-instructions.md` line 88

## Test Directory Structure

```
backend/tests/
├── conftest.py              # Shared fixtures
├── api/
│   └── routes/
│       ├── test_items.py    # Endpoint tests for items
│       ├── test_users.py    # Endpoint tests for users
│       └── test_login.py    # Authentication tests
├── crud/
│   ├── test_user.py         # CRUD operation tests for users
│   └── test_item.py         # CRUD operation tests for items
└── utils/
    ├── item.py              # Test utilities for items
    ├── user.py              # Test utilities for users
    └── utils.py             # General test utilities
```

## Key Fixtures from conftest.py

### Database Session

```python
@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        # Cleanup after all tests
```

**Scope**: `session` - shared across all tests
**Usage**: `def test_something(db: Session) -> None:`

### Test Client

```python
@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
```

**Scope**: `module` - one per test file
**Usage**: `def test_endpoint(client: TestClient) -> None:`

### Authentication Token Headers

```python
@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)

@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
```

**Usage**:
- `superuser_token_headers` - For testing admin-only endpoints
- `normal_user_token_headers` - For testing regular user permissions

**Reference**: `backend/tests/conftest.py` lines 16-42

## Required Test Cases for CRUD Resources

For each CRUD resource (e.g., items, users, posts), implement **11 test cases**:

### 1. Create Tests

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
    assert content["field2"] == data["field2"]
    assert "id" in content
    assert "owner_id" in content
```

### 2. Read Single Tests

```python
def test_read_{thing}(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    {thing} = create_random_{thing}(db)
    response = client.get(
        f"{settings.API_V1_STR}/{things}/{{thing}.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str({thing}.id)
```

### 3. Read Single Not Found

```python
def test_read_{thing}_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/{things}/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "{Thing} not found"
```

### 4. Read Single Permission Check

```python
def test_read_{thing}_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    {thing} = create_random_{thing}(db)
    response = client.get(
        f"{settings.API_V1_STR}/{things}/{{thing}.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"
```

### 5. Read List

```python
def test_read_{things}(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_{thing}(db)
    create_random_{thing}(db)
    response = client.get(
        f"{settings.API_V1_STR}/{things}/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2
```

### 6. Update Tests

```python
def test_update_{thing}(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    {thing} = create_random_{thing}(db)
    data = {"field1": "Updated value"}
    response = client.put(
        f"{settings.API_V1_STR}/{things}/{{thing}.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["field1"] == data["field1"]
    assert content["id"] == str({thing}.id)
```

### 7. Update Not Found

```python
def test_update_{thing}_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"field1": "Updated value"}
    response = client.put(
        f"{settings.API_V1_STR}/{things}/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "{Thing} not found"
```

### 8. Update Permission Check

```python
def test_update_{thing}_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    {thing} = create_random_{thing}(db)
    data = {"field1": "Updated value"}
    response = client.put(
        f"{settings.API_V1_STR}/{things}/{{thing}.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"
```

### 9. Delete Tests

```python
def test_delete_{thing}(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    {thing} = create_random_{thing}(db)
    response = client.delete(
        f"{settings.API_V1_STR}/{things}/{{thing}.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "{Thing} deleted successfully"
```

### 10. Delete Not Found

```python
def test_delete_{thing}_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/{things}/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "{Thing} not found"
```

### 11. Delete Permission Check

```python
def test_delete_{thing}_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    {thing} = create_random_{thing}(db)
    response = client.delete(
        f"{settings.API_V1_STR}/{things}/{{thing}.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"
```

**Reference**: `backend/tests/api/routes/test_items.py` (complete example with all 11 cases)

## Test Utility Pattern

Create helper functions in `backend/tests/utils/{thing}.py` for generating test data:

```python
from sqlmodel import Session
from app import crud
from app.models import {Thing}, {Thing}Create
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def create_random_{thing}(db: Session) -> {Thing}:
    user = create_random_user(db)
    owner_id = user.id
    assert owner_id is not None
    field1 = random_lower_string()
    field2 = random_lower_string()
    {thing}_in = {Thing}Create(field1=field1, field2=field2)
    return crud.create_{thing}(session=db, {thing}_in={thing}_in, owner_id=owner_id)
```

**Benefits**:
- Reusable across multiple test files
- Consistent test data generation
- Easy to modify when model changes

**Reference**: `backend/tests/utils/item.py`

## Testing Rules and Conventions

### Return Type Annotations

All test functions must have `-> None` return annotation:

```python
def test_something(client: TestClient) -> None:  # ✅ Correct
    pass

def test_something(client: TestClient):  # ❌ Wrong - missing return type
    pass
```

### Use settings.API_V1_STR for URL Prefix

Always construct URLs using the `settings.API_V1_STR` constant:

```python
from app.core.config import settings

# ✅ Correct
response = client.get(f"{settings.API_V1_STR}/items/{item.id}")

# ❌ Wrong - hardcoded prefix
response = client.get(f"/api/v1/items/{item.id}")
```

**Reference**: `backend/tests/api/routes/test_items.py` throughout

### No print() Statements

Ruff rule T201 forbids `print()` statements. Use pytest's output capture instead:

```python
# ❌ Wrong
def test_something() -> None:
    print(f"Testing with value: {value}")

# ✅ Correct - pytest captures this automatically
def test_something() -> None:
    result = some_function()
    assert result == expected, f"Expected {expected}, got {result}"
```

**Reference**: memory: python conventions (T201 rule)

### UUID Handling in Assertions

When comparing UUIDs in JSON responses, convert to string:

```python
content = response.json()
assert content["id"] == str(item.id)  # ✅ Correct
assert content["id"] == item.id       # ❌ Wrong - type mismatch
```

## Running Tests

### Full Test Suite

```bash
# Start required services
docker compose up -d db mailcatcher

# Run migrations and seed data
cd backend && uv run bash scripts/prestart.sh && cd ..

# Run all tests with coverage
cd backend && uv run bash scripts/tests-start.sh && cd ..

# Check coverage threshold
cd backend && uv run coverage report --fail-under=90 && cd ..
```

**Reference**: `.github/copilot-instructions.md` lines 74-88, memory: build and test

### Run Specific Test File

```bash
cd backend
uv run pytest tests/api/routes/test_items.py -v
cd ..
```

### Run Specific Test Function

```bash
cd backend
uv run pytest tests/api/routes/test_items.py::test_create_item -v
cd ..
```

### Run with Output

```bash
cd backend
uv run pytest tests/api/routes/test_items.py -v -s
cd ..
```

### Check Coverage for Specific Module

```bash
cd backend
uv run coverage run -m pytest tests/api/routes/test_items.py
uv run coverage report --include="app/api/routes/items.py"
cd ..
```

## Testing Different Scenarios

### Testing Authentication

```python
def test_access_token_with_invalid_credentials(client: TestClient) -> None:
    data = {"username": "invalid@example.com", "password": "wrongpassword"}
    response = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=data,
    )
    assert response.status_code == 400
```

### Testing Validation Errors (422)

Test invalid data that fails Pydantic validation:

**Empty/Missing Required Fields**:
```python
def test_create_item_empty_title(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": ""}  # Empty string fails min_length=1
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422  # Validation error
    content = response.json()
    assert "detail" in content
```

**Wrong Data Types**:
```python
def test_create_item_wrong_type(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": 123}  # Integer instead of string
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422
```

**Field Length Violations**:
```python
def test_create_item_title_too_long(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "x" * 300}  # Exceeds max_length=255
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422
```

### Testing Pagination

```python
def test_read_items_with_pagination(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Create 5 items
    for _ in range(5):
        create_random_item(db)

    # Get first page
    response = client.get(
        f"{settings.API_V1_STR}/items/?skip=0&limit=2",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) == 2
    assert content["count"] >= 5

    # Get second page
    response = client.get(
        f"{settings.API_V1_STR}/items/?skip=2&limit=2",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) == 2
```

### Testing Unique Constraints (400)

Test duplicate data when unique constraints exist:

```python
def test_create_user_duplicate_email(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Create first user
    email = "test@example.com"
    data = {"email": email, "password": "password123"}
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200

    # Try to create duplicate
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "already exists" in content["detail"].lower()
```

**Reference**: `backend/tests/api/routes/test_users.py` for duplicate email tests

### Testing Unauthenticated Requests (401)

Test endpoints without authentication token:

```python
def test_create_item_unauthenticated(client: TestClient) -> None:
    data = {"title": "Test Item", "description": "Test"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        json=data,
        # No headers - unauthenticated
    )
    assert response.status_code == 401
    content = response.json()
    assert content["detail"] == "Not authenticated"
```

### Testing Query Parameters and Filters

If your endpoint supports filtering or search:

```python
def test_read_items_with_filter(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Create items with different attributes
    item1 = create_random_item(db)
    item2 = create_random_item(db)

    # Test filter query parameter
    response = client.get(
        f"{settings.API_V1_STR}/items/?status=active",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    # Verify filtering works correctly
    for item in content["data"]:
        assert item["status"] == "active"
```

**Note**: Only add filter tests if your endpoint actually implements filtering.

### Testing CRUD Operations Directly

For testing CRUD functions without HTTP layer:

```python
from app import crud
from app.models import ItemCreate

def test_crud_create_item(db: Session) -> None:
    user = create_random_user(db)
    item_in = ItemCreate(title="Test", description="Test description")
    item = crud.create_item(session=db, item_in=item_in, owner_id=user.id)
    assert item.title == "Test"
    assert item.owner_id == user.id
```

## Common Testing Pitfalls

- **Not using `settings.API_V1_STR`** - Always use the constant for URL construction
- **Missing `-> None` return annotation** - Mypy will complain
- **Using `print()` for debugging** - Use pytest's `-s` flag and assertions instead
- **Forgetting to start database** - Tests require `docker compose up -d db mailcatcher`
- **Not running prestart.sh** - Migrations must be applied before tests
- **UUID type mismatches** - Convert to string when comparing JSON responses
- **Testing without isolation** - Use `create_random_{thing}` helpers to avoid test interference
- **Not achieving ≥90% coverage** - CI will fail; add missing test cases

## Debugging Test Failures

### View Detailed Output

```bash
cd backend
uv run pytest tests/api/routes/test_items.py -vv
cd ..
```

### Stop on First Failure

```bash
cd backend
uv run pytest tests/api/routes/test_items.py -x
cd ..
```

### Run Last Failed Tests

```bash
cd backend
uv run pytest --lf
cd ..
```

### Show Local Variables on Failure

```bash
cd backend
uv run pytest tests/api/routes/test_items.py -l
cd ..
```

### Run with pdb on Failure

```python
# Add this to test
import pdb; pdb.set_trace()

# Or run with --pdb
cd backend
uv run pytest tests/api/routes/test_items.py --pdb
cd ..
```

## Coverage Reports

### Generate HTML Coverage Report

```bash
cd backend
uv run coverage run -m pytest
uv run coverage html
cd ..
# Open backend/htmlcov/index.html in browser
```

### Show Missing Lines

```bash
cd backend
uv run coverage report -m
cd ..
```

### Coverage for Specific Files

```bash
cd backend
uv run coverage report --include="app/api/routes/*.py"
cd ..
```

## Testing Checklist

- [ ] Created test file in appropriate directory (`api/routes/`, `crud/`, `utils/`)
- [ ] Imported required fixtures: `client`, `db`, `superuser_token_headers`, `normal_user_token_headers`
- [ ] Implemented 11 test cases for CRUD resource (create, read, read-not-found, read-permissions, read-all, update, update-not-found, update-permissions, delete, delete-not-found, delete-permissions)
- [ ] Created test utility helper in `tests/utils/{thing}.py`
- [ ] All test functions have `-> None` return annotation
- [ ] Used `settings.API_V1_STR` for all API URLs
- [ ] Converted UUIDs to strings in assertions: `str(item.id)`
- [ ] No `print()` statements (T201 rule)
- [ ] Started database: `docker compose up -d db mailcatcher`
- [ ] Ran migrations: `cd backend && uv run bash scripts/prestart.sh`
- [ ] Ran tests: `cd backend && uv run bash scripts/tests-start.sh`
- [ ] Verified ≥90% coverage: `cd backend && uv run coverage report --fail-under=90`
- [ ] All tests passing
