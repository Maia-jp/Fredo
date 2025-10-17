# Contributing to Fredo

First off, thank you for considering contributing to Fredo! 🎬

## Code of Conduct

This project follows a simple rule: **Be kind and respectful.**

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues. When creating a bug report, include:

- A clear and descriptive title
- Exact steps to reproduce the problem
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, Fredo version)
- Any relevant error messages or logs

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- A detailed description of the proposed feature
- Examples of how the feature would be used
- Why this enhancement would be useful

### Pull Requests

1. Fork the repo and create your branch from `main`
2. Install dependencies: `pip3 install -e .`
3. Make your changes
4. Test your changes thoroughly
5. Update documentation if needed
6. Follow the coding style (see below)
7. Commit your changes with clear commit messages
8. Push to your fork and submit a pull request

## Coding Style

Fredo follows these principles:

- **Simple** - Keep it straightforward
- **Elegant** - Write clean, readable code
- **Rock-solid** - Handle errors gracefully

### Python Style Guide

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable names

### Example

```python
def search_snippets(
    query: str,
    language: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> List[Snippet]:
    """Search for snippets with optional filters.
    
    Args:
        query: Search query string
        language: Filter by language
        tags: Filter by tags
        
    Returns:
        List of matching snippets
    """
    # Implementation
    pass
```

## Project Structure

```
fredo/
├── fredo/
│   ├── cli/          # CLI commands and interactive UI
│   ├── core/         # Core functionality (database, search, runner)
│   ├── integrations/ # External integrations (GitHub Gist)
│   └── utils/        # Utilities (config, editor)
├── docs/             # Documentation
└── tests/            # Tests (if/when added)
```

## Testing

While comprehensive tests are not yet in place, please:

1. Test your changes manually
2. Try edge cases
3. Test on different operating systems if possible
4. Verify existing functionality still works

## Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests after the first line

Examples:
```
Add fuzzy search for tags

Fix editor not opening on Windows

Improve error messages for Gist operations
```

## Documentation

- Update README.md if you change functionality
- Update docs/ files if needed
- Add examples for new features
- Keep the Quick Start guide up to date

## Questions?

Feel free to open an issue with the label "question" if you need clarification on anything.

Thank you for contributing! 🙏

