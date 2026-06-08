# Testing Strategy — Electronic Queue System

## Requirements

- **Minimum coverage:** 70% (enforced by `--cov-fail-under=70` in pytest)
- **Target tests:** 200+ unit + integration tests
- **Framework:** pytest + pytest-cov
- **Reports:** JUnit XML (`reports/junit.xml`) + Coverage XML/HTML (`reports/`)

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures (fresh repos, services, seeded containers)
├── unit/
│   ├── test_models.py              # Ticket, ServiceWindow, ServiceType, Notification
│   ├── test_queue_service.py       # QueueService — all methods, edge cases
│   ├── test_repositories.py        # InMemory* repositories — CRUD, filters
│   ├── test_services.py            # WindowService, ServiceTypeService
│   └── test_strategies_observers.py # Strategy sorting, Observer events
└── integration/
    ├── test_api.py                 # Flask HTTP endpoints (TestClient)
    └── test_queue_flow.py          # End-to-end queue workflows
```

## Rules for AI Test Generation

1. **TDD** — write test first, then implementation
2. **Each public method** gets at minimum: happy path, edge case, error case
3. **Use fixtures** from `conftest.py` — never instantiate repos/services directly in tests
4. **Mock nothing in unit tests** — use real InMemory implementations (they are fast and deterministic)
5. **Use `pytest.raises`** for all error/exception paths
6. **Parametrize** repetitive tests: `@pytest.mark.parametrize`

## Running Tests

```bash
# All tests with coverage report
pytest --cov=src --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --junit-xml=reports/junit.xml -v

# Unit only
pytest tests/unit/ -v

# Integration only
pytest tests/integration/ -v

# Specific file
pytest tests/unit/test_queue_service.py -v
```

## Coverage Report

After running, open `reports/coverage_html/index.html` to see line-by-line coverage.
Red lines = uncovered. These must be covered to pass Quality Gate.

## SonarQube Integration

CI pipeline sends `reports/coverage.xml` and `reports/junit.xml` to SonarCloud automatically.
Quality Gate blocks merge if coverage < 70% or Bugs > 0.
