# ContextPilot Testing Guide

## Test Suite Overview

The ContextPilot backend includes comprehensive tests covering models, storage, and composition logic.

### Test Files

| File | Purpose | Dependencies |
|------|---------|--------------|
| `test_unit_lite.py` | Unit tests (no model loading) | ✅ Fast, no internet |
| `test_integration.py` | API integration tests | ⚠️ Requires model |
| `test_functional.py` | Functional smoke tests | ✅ Fast, no internet |
| `test_api.py` | Legacy test script | ⚠️ Requires model |

## Running Tests

### Quick Test (Recommended)
```bash
./run_tests.sh
```

### Unit Tests Only
```bash
python -m pytest test_unit_lite.py -v
```

### Functional Tests
```bash
python test_functional.py
```

### All Tests (with model)
```bash
python -m pytest -v
```

## Test Coverage

### ✅ Models (8 tests)
- ContextUnit creation and validation
- ContextUnitCreate/Update schemas
- TaskRequest validation
- Confidence bounds checking

### ✅ Storage (14 tests)
- Add/get/update/delete operations
- Embedding storage
- Supersede functionality
- Active vs. superseded filtering
- Edge cases (nonexistent IDs, etc.)

### ✅ Composer (4 tests)
- Empty context handling
- Single and multiple context composition
- Prompt formatting
- Compact format generation

**Total: 26 unit tests** (all passing ✓)

## VS Code Integration

### Debug Configuration
Use "Python: Backend Tests" launch configuration to debug tests in VS Code.

### Run Tests from Command Palette
1. `Cmd+Shift+P` → "Tasks: Run Task"
2. Select "Test Backend"

## CI/CD Integration

The test suite is designed for CI/CD pipelines:

```yaml
# .github/workflows/test.yml example
- name: Run tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest test_unit_lite.py test_functional.py -v
```

## Test Results

Last run: **26 passed in 0.18s** ✅

```
test_unit_lite.py::TestModels::test_context_unit_creation PASSED
test_unit_lite.py::TestModels::test_context_unit_defaults PASSED
test_unit_lite.py::TestModels::test_context_unit_validation_confidence_min PASSED
test_unit_lite.py::TestModels::test_context_unit_validation_confidence_max PASSED
test_unit_lite.py::TestModels::test_context_unit_create_schema PASSED
test_unit_lite.py::TestModels::test_context_unit_update_schema PASSED
test_unit_lite.py::TestModels::test_task_request_schema PASSED
test_unit_lite.py::TestModels::test_task_request_defaults PASSED
test_unit_lite.py::TestStorage::test_add_context_without_embedding PASSED
test_unit_lite.py::TestStorage::test_add_context_with_embedding PASSED
test_unit_lite.py::TestStorage::test_list_contexts_empty PASSED
test_unit_lite.py::TestStorage::test_list_contexts_multiple PASSED
test_unit_lite.py::TestStorage::test_list_contexts_exclude_superseded PASSED
test_unit_lite.py::TestStorage::test_list_contexts_include_superseded PASSED
test_unit_lite.py::TestStorage::test_update_context PASSED
test_unit_lite.py::TestStorage::test_update_nonexistent_context PASSED
test_unit_lite.py::TestStorage::test_delete_context PASSED
test_unit_lite.py::TestStorage::test_delete_nonexistent_context PASSED
test_unit_lite.py::TestStorage::test_delete_context_with_embedding PASSED
test_unit_lite.py::TestStorage::test_supersede_context PASSED
test_unit_lite.py::TestStorage::test_supersede_nonexistent_context PASSED
test_unit_lite.py::TestStorage::test_list_with_embeddings PASSED
test_unit_lite.py::TestComposer::test_compose_empty PASSED
test_unit_lite.py::TestComposer::test_compose_with_single_context PASSED
test_unit_lite.py::TestComposer::test_compose_with_multiple_contexts PASSED
test_unit_lite.py::test_imports PASSED
```

## Known Issues

### Model Download
Tests requiring `RelevanceEngine` need internet to download the sentence-transformers model (~80MB) on first run. Use `test_unit_lite.py` for offline testing.

### Pydantic Warnings
Some deprecation warnings appear for `json_encoders`. These are informational and don't affect functionality. Will be fixed in future updates.

## Adding New Tests

### Example Test
```python
def test_new_feature():
    """Test new feature."""
    # Arrange
    context = ContextUnit(type=ContextType.FACT, content="Test")
    
    # Act
    result = some_function(context)
    
    # Assert
    assert result is not None
```

### Test Naming Convention
- `test_*` for test functions
- `Test*` for test classes
- Use descriptive names: `test_context_creation_with_valid_data`

## Performance

- Unit tests: ~0.2 seconds
- Functional tests: ~0.1 seconds
- Full suite (with model): ~5-10 seconds (first run with download)

## Troubleshooting

### Import Errors
```bash
# Ensure you're in the venv
source venv/bin/activate
pip install -r requirements.txt
```

### Module Not Found
```bash
# Run from backend directory
cd backend
python -m pytest test_unit_lite.py
```

### Network Issues
Use offline tests only:
```bash
python -m pytest test_unit_lite.py test_functional.py
```
