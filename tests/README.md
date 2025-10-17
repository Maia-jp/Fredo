# Fredo Test Suite

Comprehensive unit tests for the Fredo snippet manager.

## Structure

The test suite is organized into the following modules:

- **`test_models.py`**: Tests for the `Snippet` data model
  - Snippet creation and validation
  - Tag normalization and validation
  - Serialization/deserialization
  - File extension mapping
  - Edge cases with Unicode and special characters

- **`test_database.py`**: Tests for database operations
  - Database initialization and schema creation
  - CRUD operations (Create, Read, Update, Delete)
  - Search and filtering functionality
  - Tag aggregation
  - Transaction handling
  - SQL injection prevention

- **`test_runner.py`**: Tests for snippet execution
  - Language detection (shebang, Pygments, explicit)
  - Execution feasibility checks
  - Snippet execution in different modes (current/isolated)
  - Temporary file handling and cleanup
  - Error handling
  - Support for multiple languages

- **`test_search.py`**: Tests for fuzzy search engine
  - Basic search functionality
  - Scoring algorithm (exact match, substring, fuzzy)
  - Search filters (language, tags)
  - Result sorting and limiting
  - Performance with large datasets

- **`test_config.py`**: Tests for configuration management
  - Config loading and saving
  - Default value handling
  - Environment variable fallbacks
  - Editor detection
  - TOML serialization

- **`test_editor.py`**: Tests for editor integration
  - Editor command detection
  - Temporary file creation
  - Content editing workflow
  - Comment character detection
  - Message handling and cleanup

- **`test_gist.py`**: Tests for GitHub Gist integration
  - Gist creation and updates
  - Gist retrieval and listing
  - Gist to Snippet conversion
  - Error handling (authentication, network, API limits)
  - Public/private Gist handling

- **`conftest.py`**: Shared pytest fixtures and configuration
  - Temporary directory and database fixtures
  - Sample snippet fixtures
  - Mock GitHub client fixtures
  - Environment cleanup

## Running Tests

### Install Dependencies

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Module

```bash
pytest tests/test_models.py
pytest tests/test_database.py
```

### Run Specific Test Class or Function

```bash
pytest tests/test_models.py::TestSnippetCreation
pytest tests/test_models.py::TestSnippetCreation::test_create_snippet_with_required_fields
```

### Run Tests with Coverage

```bash
pytest --cov=fredo --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run Tests in Verbose Mode

```bash
pytest -v
```

### Run Tests and Show Print Statements

```bash
pytest -s
```

### Run Specific Markers

```bash
# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"

# Run integration tests
pytest -m integration
```

### Run Tests with Specific Python Version

```bash
python3.12 -m pytest
```

## Test Coverage

The test suite aims for high coverage:

- **Models**: 100% coverage of data validation and serialization
- **Database**: Comprehensive CRUD operations and edge cases
- **Runner**: Language detection and execution (mocked for safety)
- **Search**: Complete scoring algorithm and filtering logic
- **Config**: Configuration management and environment handling
- **Editor**: Editor integration workflow (mocked subprocess calls)
- **Gist**: GitHub API interactions (fully mocked)

## Writing New Tests

### Guidelines

1. **Follow the AAA pattern**: Arrange, Act, Assert
2. **One assertion per test**: Keep tests focused
3. **Use descriptive names**: `test_<what>_<condition>_<expected>`
4. **Test both happy and sad paths**: Success and error cases
5. **Test edge cases**: Empty inputs, Unicode, very long strings, etc.
6. **Use fixtures**: Reuse common setup via `conftest.py`
7. **Mock external dependencies**: Network, file system, subprocess

### Example Test

```python
def test_create_snippet_with_tags(db: Database):
    """Test creating a snippet with tags."""
    # Arrange
    snippet = Snippet(
        name="test",
        content="print('hello')",
        tags=["python", "test"],
    )
    
    # Act
    result = db.create(snippet)
    
    # Assert
    assert result.tags == ["python", "test"]
    assert db.get_by_name("test") is not None
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- **Fast execution**: Most tests complete in seconds
- **Isolated**: Tests don't depend on external services
- **Deterministic**: No flaky tests
- **Clean**: Proper setup and teardown

## Troubleshooting

### Tests Fail Due to Missing Dependencies

```bash
pip install -e ".[dev]"
```

### Tests Fail Due to Database Locks

The test suite uses isolated temporary databases. If you encounter locks:

```bash
# Clean up any stray processes
pkill -f pytest
```

### Import Errors

Make sure you're running tests from the project root:

```bash
cd /path/to/fredo
pytest
```

## Test Metrics

- **Total Tests**: 250+
- **Test Modules**: 9
- **Coverage**: >90% (target)
- **Execution Time**: <30 seconds (full suite)

## Future Enhancements

- [ ] Add integration tests with real GitHub API (optional, behind flag)
- [ ] Add performance benchmarks for search
- [ ] Add CLI command tests
- [ ] Add parallel test execution
- [ ] Add mutation testing

