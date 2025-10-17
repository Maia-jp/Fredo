"""Pytest configuration and shared fixtures."""

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, Mock

import pytest
from github import Github
from github.Gist import Gist as GithubGist

from fredo.core.database import Database
from fredo.core.models import Snippet
from fredo.utils.config import ConfigManager, FredoConfig


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp(prefix="fredo_test_"))
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Create a temporary database path."""
    return temp_dir / "test_snippets.db"


@pytest.fixture
def test_config(temp_dir: Path, temp_db_path: Path) -> FredoConfig:
    """Create a test configuration."""
    return FredoConfig(
        database_path=str(temp_db_path),
        editor="vim",
        github_token="test_token_123",
        default_execution_mode="current",
        gist_private_by_default=True,
    )


@pytest.fixture
def config_manager(
    temp_dir: Path, test_config: FredoConfig, monkeypatch
) -> ConfigManager:
    """Create a ConfigManager with test configuration."""
    config_dir = temp_dir / ".config" / "fredo"
    config_dir.mkdir(parents=True, exist_ok=True)

    cm = ConfigManager()
    cm.config_dir = config_dir
    cm.config_file = config_dir / "config.toml"
    cm._config = test_config
    cm.save(test_config)

    return cm


@pytest.fixture
def db(temp_db_path: Path, config_manager: ConfigManager) -> Database:
    """Create a test database instance."""
    database = Database()
    database.db_path = temp_db_path
    database.init_db()
    return database


@pytest.fixture
def sample_snippet() -> Snippet:
    """Create a sample snippet for testing."""
    return Snippet(
        id="test-id-123",
        name="test-snippet",
        content='#!/usr/bin/env python3\nprint("Hello, World!")',
        language="python",
        tags=["test", "hello-world"],
        execution_mode="current",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_bash_snippet() -> Snippet:
    """Create a sample bash snippet for testing."""
    return Snippet(
        name="test-bash",
        content='#!/bin/bash\necho "Hello from Bash"',
        language="bash",
        tags=["shell", "test"],
        execution_mode="isolated",
    )


@pytest.fixture
def sample_js_snippet() -> Snippet:
    """Create a sample JavaScript snippet for testing."""
    return Snippet(
        name="test-js",
        content='console.log("Hello from Node.js");',
        language="javascript",
        tags=["js", "node"],
        execution_mode="current",
    )


@pytest.fixture
def multiple_snippets() -> list[Snippet]:
    """Create multiple snippets for testing search and list operations."""
    return [
        Snippet(
            name="python-hello",
            content='print("Hello from Python")',
            language="python",
            tags=["python", "hello"],
        ),
        Snippet(
            name="python-calc",
            content="result = 2 + 2\nprint(result)",
            language="python",
            tags=["python", "math"],
        ),
        Snippet(
            name="bash-script",
            content='#!/bin/bash\necho "Hello from Bash"',
            language="bash",
            tags=["shell", "hello"],
        ),
        Snippet(
            name="docker-cleanup",
            content="docker system prune -af",
            language="bash",
            tags=["docker", "cleanup"],
        ),
        Snippet(
            name="js-fetch",
            content='fetch("https://api.example.com").then(r => r.json())',
            language="javascript",
            tags=["javascript", "api"],
        ),
    ]


@pytest.fixture
def mock_github() -> Mock:
    """Create a mock GitHub client."""
    mock_gh = Mock(spec=Github)
    mock_user = Mock()
    mock_user.login = "testuser"
    mock_gh.get_user.return_value = mock_user
    return mock_gh


@pytest.fixture
def mock_gist() -> Mock:
    """Create a mock GitHub Gist."""
    mock_gist = Mock(spec=GithubGist)
    mock_gist.id = "test_gist_id_123"
    mock_gist.html_url = "https://gist.github.com/testuser/test_gist_id_123"
    mock_gist.description = "Test Gist (python) - Tags: test, example"
    
    # Mock file
    mock_file = Mock()
    mock_file.filename = "test_snippet.py"
    mock_file.content = 'print("Hello from Gist")'
    mock_file.language = "Python"
    
    mock_gist.files = {"test_snippet.py": mock_file}
    
    return mock_gist


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment variables for consistent tests."""
    env_vars = ["VISUAL", "EDITOR", "GITHUB_TOKEN"]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


@pytest.fixture(autouse=True)
def reset_global_instances():
    """Reset global instances between tests to avoid state pollution."""
    # Import here to avoid circular imports
    from fredo.core import database, runner, search
    from fredo.integrations import gist
    from fredo.utils import config, editor
    
    # Reset database instance
    database.db.db_path = None
    
    # Reset config manager
    config.config_manager._config = None
    
    # Reset gist manager
    gist.gist_manager._github = None
    
    yield
    
    # Cleanup after test
    database.db.db_path = None
    config.config_manager._config = None
    gist.gist_manager._github = None


@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run for successful execution."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Success output"
    mock_result.stderr = ""
    return mock_result


@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.run for failed execution."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Error output"
    return mock_result

