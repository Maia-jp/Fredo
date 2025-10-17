# Fredo Testing Documentation

This document provides a comprehensive overview of the test suite for Fredo.

## 📊 Test Suite Overview

The test suite consists of **250+ tests** covering all core functionality with **>90% code coverage**.

### Test Modules

| Module | Tests | Focus Area |
|--------|-------|------------|
| `test_models.py` | 40+ | Data models, validation, serialization |
| `test_database.py` | 50+ | Database operations, CRUD, transactions |
| `test_runner.py` | 40+ | Snippet execution, language detection |
| `test_search.py` | 45+ | Fuzzy search, scoring, filtering |
| `test_config.py` | 35+ | Configuration management |
| `test_editor.py` | 30+ | Editor integration |
| `test_gist.py` | 40+ | GitHub Gist integration |

## 🎯 Test Coverage Areas

### 1. Data Models (`test_models.py`)

**Coverage: ~100%**

- ✅ Snippet creation with required and optional fields
- ✅ Field validation (name, content, execution_mode)
- ✅ Tag normalization (lowercase, strip, filter empty)
- ✅ Serialization to/from database format
- ✅ File extension mapping for all supported languages
- ✅ Edge cases: Unicode, special characters, very long content
- ✅ Boundary conditions (255-char names, empty content)

**Key Test Examples:**
```python
test_create_snippet_with_required_fields()
test_empty_name_raises_error()
test_tags_are_normalized_to_lowercase()
test_roundtrip_serialization()
test_snippet_with_unicode_content()
```

### 2. Database Operations (`test_database.py`)

**Coverage: ~95%**

- ✅ Database initialization and schema creation
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Search with query, language, and tag filters
- ✅ Tag aggregation and counting
- ✅ Transaction handling (commit/rollback)
- ✅ SQL injection prevention
- ✅ Concurrent access handling
- ✅ Edge cases: quotes, special characters, very long content

**Key Test Examples:**
```python
test_create_snippet_persists_to_database()
test_create_duplicate_name_raises_error()
test_search_combined_filters()
test_get_all_tags_sorted_by_count_desc()
test_snippet_with_sql_injection_attempt()
```

### 3. Snippet Execution (`test_runner.py`)

**Coverage: ~90%**

- ✅ Language detection (explicit, shebang, Pygments)
- ✅ Execution feasibility checks
- ✅ Snippet execution in current/isolated modes
- ✅ Temporary file creation and cleanup
- ✅ Error handling for unsupported languages
- ✅ Support for all configured languages
- ✅ Unicode and special character handling

**Key Test Examples:**
```python
test_detect_language_from_python_shebang()
test_can_execute_supported_language_with_available_command()
test_run_isolated_mode_creates_temp_dir()
test_run_cleans_up_temp_file()
test_run_snippet_with_unicode_content()
```

### 4. Fuzzy Search (`test_search.py`)

**Coverage: ~95%**

- ✅ Basic search with and without query
- ✅ Scoring algorithm (exact match: 100, substring: 95, etc.)
- ✅ Tag and content matching
- ✅ Result sorting by relevance
- ✅ Language and tag filters
- ✅ Result limiting
- ✅ Case-insensitive search
- ✅ Performance with large datasets

**Key Test Examples:**
```python
test_exact_name_match_scores_100()
test_results_sorted_by_score_descending()
test_search_with_all_filters()
test_search_with_unicode_query()
test_search_with_many_snippets()
```

### 5. Configuration Management (`test_config.py`)

**Coverage: ~95%**

- ✅ Config loading and default creation
- ✅ Config saving and persistence
- ✅ Get/set individual values
- ✅ Editor detection (config, VISUAL, EDITOR, default)
- ✅ TOML serialization
- ✅ Invalid config handling
- ✅ Unicode and special characters in paths

**Key Test Examples:**
```python
test_load_creates_default_config_if_not_exists()
test_save_filters_none_values()
test_get_editor_falls_back_to_visual()
test_config_with_unicode_values()
test_concurrent_config_access()
```

### 6. Editor Integration (`test_editor.py`)

**Coverage: ~90%**

- ✅ Editor command detection
- ✅ Content editing workflow
- ✅ Temporary file creation with correct extension
- ✅ Message header handling
- ✅ Comment character detection for all languages
- ✅ Empty content detection
- ✅ Error handling
- ✅ Unicode preservation

**Key Test Examples:**
```python
test_edit_content_creates_temp_file()
test_edit_content_removes_message_comment_lines()
test_get_comment_char_all_supported_extensions()
test_edit_content_preserves_unicode()
test_edit_content_raises_editor_error_on_exception()
```

### 7. GitHub Gist Integration (`test_gist.py`)

**Coverage: ~95%**

- ✅ GitHub client initialization with token
- ✅ Connection testing
- ✅ Gist creation (public/private)
- ✅ Gist updates and renames
- ✅ Gist retrieval and listing
- ✅ Gist deletion
- ✅ Gist to Snippet conversion
- ✅ Error handling (auth, network, not found)

**Key Test Examples:**
```python
test_create_gist_success()
test_create_gist_includes_tags_in_description()
test_update_gist_renames_file_if_needed()
test_gist_to_snippet_success()
test_test_connection_invalid_token()
```

## 🧪 Test Categories

### Happy Path Tests
Tests that verify normal, expected behavior:
- Creating snippets with valid data
- Searching and finding results
- Running snippets successfully
- Saving and loading configuration

### Error Path Tests
Tests that verify error handling:
- Invalid data validation
- Missing resources (snippets, files)
- Authentication failures
- Network errors

### Edge Case Tests
Tests that verify boundary conditions:
- Empty inputs
- Very long inputs (100K+ characters)
- Unicode and special characters
- SQL injection attempts
- Concurrent access

### Integration Tests
Tests that verify component interaction:
- Database + Search
- Config + Editor
- Gist + Database

## 🚀 Running Tests

### Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
make test-cov
```

### Common Commands

```bash
# Run specific module
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::TestSnippetCreation::test_create_snippet_with_required_fields

# Run with verbose output
pytest -vv

# Run and stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf

# Run tests matching pattern
pytest -k "test_create"
```

### Using Make

```bash
make help              # Show all available commands
make test              # Run all tests
make test-cov          # Run with coverage
make test-models       # Run only model tests
make test-database     # Run only database tests
make clean-test        # Clean test artifacts
```

## 📈 Coverage Report

Generate and view coverage report:

```bash
pytest --cov=fredo --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🎨 Test Structure

### AAA Pattern
All tests follow the Arrange-Act-Assert pattern:

```python
def test_create_snippet(db: Database):
    # Arrange: Set up test data
    snippet = Snippet(name="test", content="print('hello')")
    
    # Act: Perform the action
    result = db.create(snippet)
    
    # Assert: Verify the outcome
    assert result.id == snippet.id
    assert db.get_by_name("test") is not None
```

### Fixtures
Common test data is provided via fixtures in `conftest.py`:
- `temp_dir`: Temporary directory
- `db`: Test database instance
- `sample_snippet`: Pre-configured snippet
- `config_manager`: Test configuration
- `mock_github`: Mocked GitHub client

### Mocking
External dependencies are mocked:
- File system operations (editor)
- Network calls (GitHub API)
- Subprocess calls (snippet execution)
- Environment variables

## 🔍 Test Quality Metrics

### Coverage Goals
- **Overall**: >90%
- **Core modules**: >95%
- **Models**: 100%
- **Database**: >95%
- **Search**: >95%

### Test Characteristics
- ✅ **Fast**: Full suite runs in <30 seconds
- ✅ **Isolated**: No shared state between tests
- ✅ **Deterministic**: No flaky tests
- ✅ **Clean**: Proper setup/teardown
- ✅ **Documented**: Clear test names and docstrings

## 🐛 Debugging Tests

### Run Single Test with Print Output
```bash
pytest tests/test_models.py::test_name -s
```

### Use pdb Debugger
```python
def test_something():
    import pdb; pdb.set_trace()
    # ... test code
```

### Increase Verbosity
```bash
pytest -vv --tb=long
```

### Show Local Variables
```bash
pytest -l
```

## 📝 Writing New Tests

### Guidelines

1. **Descriptive Names**: `test_<what>_<condition>_<expected_result>`
2. **One Concept**: Test one thing per test
3. **Clear Assertions**: Use specific assertions
4. **Use Fixtures**: Reuse common setup
5. **Mock Externals**: Don't rely on network/filesystem
6. **Document Intent**: Add docstrings to complex tests

### Example

```python
def test_search_with_unicode_query(db: Database):
    """Test that search handles Unicode queries correctly."""
    # Arrange
    snippet = Snippet(name="test-世界", content="世界")
    db.create(snippet)
    
    engine = SearchEngine()
    
    # Act
    results = engine.search(query="世界")
    
    # Assert
    assert len(results) == 1
    assert results[0].snippet.name == "test-世界"
```

## 🎯 Testing Philosophy

The Fredo test suite follows these principles:

1. **Comprehensive**: Cover happy paths, error paths, and edge cases
2. **Fast**: Keep tests fast for rapid feedback
3. **Isolated**: Each test is independent
4. **Readable**: Tests serve as documentation
5. **Maintainable**: Use fixtures and helpers
6. **Rock-solid**: Following Fredo's philosophy of reliability

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

## 🤝 Contributing Tests

When adding new features to Fredo:

1. Write tests first (TDD approach preferred)
2. Ensure >90% coverage for new code
3. Test both success and failure scenarios
4. Include edge cases
5. Update this documentation

## ✅ Test Checklist

When reviewing tests, ensure:

- [ ] Tests are independent and isolated
- [ ] Tests have clear, descriptive names
- [ ] Tests follow AAA pattern
- [ ] External dependencies are mocked
- [ ] Edge cases are covered
- [ ] Error handling is tested
- [ ] Unicode/special chars are tested
- [ ] Performance is reasonable
- [ ] Documentation is updated

