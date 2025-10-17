"""Tests for the ConfigManager."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from fredo.utils.config import ConfigManager, FredoConfig


class TestFredoConfig:
    """Test FredoConfig model."""

    def test_create_default_config(self):
        """Test creating config with default values."""
        config = FredoConfig()
        
        assert config.database_path.endswith("snippets.db")
        assert config.editor is None
        assert config.github_token is None
        assert config.default_execution_mode == "current"
        assert config.gist_private_by_default is True

    def test_create_config_with_custom_values(self, temp_dir: Path):
        """Test creating config with custom values."""
        config = FredoConfig(
            database_path=str(temp_dir / "custom.db"),
            editor="nvim",
            github_token="ghp_test123",
            default_execution_mode="isolated",
            gist_private_by_default=False,
        )
        
        assert str(temp_dir / "custom.db") in config.database_path
        assert config.editor == "nvim"
        assert config.github_token == "ghp_test123"
        assert config.default_execution_mode == "isolated"
        assert config.gist_private_by_default is False

    def test_config_validates_on_assignment(self):
        """Test that config validates on assignment."""
        config = FredoConfig()
        
        # Valid assignment
        config.default_execution_mode = "isolated"
        assert config.default_execution_mode == "isolated"

    def test_config_model_dump(self):
        """Test converting config to dict."""
        config = FredoConfig(
            editor="vim",
            github_token="test_token",
        )
        
        data = config.model_dump()
        
        assert "database_path" in data
        assert data["editor"] == "vim"
        assert data["github_token"] == "test_token"


class TestConfigManagerInitialization:
    """Test ConfigManager initialization."""

    def test_config_manager_initializes(self, temp_dir: Path):
        """Test that ConfigManager initializes correctly."""
        cm = ConfigManager()
        
        assert cm.config_dir is not None
        assert cm.config_file is not None
        assert cm._config is None  # Not loaded yet

    def test_config_manager_paths(self):
        """Test ConfigManager paths."""
        cm = ConfigManager()
        
        assert cm.config_dir == Path.home() / ".config" / "fredo"
        assert cm.config_file == cm.config_dir / "config.toml"

    def test_ensure_config_dir_creates_directory(self, temp_dir: Path):
        """Test that ensure_config_dir creates directory."""
        config_dir = temp_dir / "config" / "fredo"
        
        cm = ConfigManager()
        cm.config_dir = config_dir
        cm.ensure_config_dir()
        
        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_ensure_config_dir_idempotent(self, temp_dir: Path):
        """Test that ensure_config_dir is idempotent."""
        config_dir = temp_dir / "config" / "fredo"
        
        cm = ConfigManager()
        cm.config_dir = config_dir
        
        # Call multiple times
        cm.ensure_config_dir()
        cm.ensure_config_dir()
        cm.ensure_config_dir()
        
        assert config_dir.exists()

    def test_ensure_data_dir_creates_directory(self, temp_dir: Path, monkeypatch):
        """Test that ensure_data_dir creates directory."""
        data_dir = temp_dir / "data"
        
        monkeypatch.setattr(Path, "home", lambda: temp_dir)
        
        cm = ConfigManager()
        result = cm.ensure_data_dir()
        
        expected_dir = temp_dir / ".local" / "share" / "fredo"
        assert expected_dir.exists()
        assert result == expected_dir


class TestConfigManagerLoad:
    """Test loading configuration."""

    def test_load_creates_default_config_if_not_exists(
        self, temp_dir: Path
    ):
        """Test that load creates default config if file doesn't exist."""
        cm = ConfigManager()
        cm.config_dir = temp_dir / "config"
        cm.config_file = cm.config_dir / "config.toml"
        
        config = cm.load()
        
        assert config is not None
        assert isinstance(config, FredoConfig)
        assert cm.config_file.exists()

    def test_load_reads_existing_config(self, config_manager: ConfigManager):
        """Test that load reads existing config file."""
        config = config_manager.load()
        
        assert config is not None
        assert config.editor == "vim"
        assert config.github_token == "test_token_123"

    def test_load_caches_config(self, config_manager: ConfigManager):
        """Test that load caches config in memory."""
        config1 = config_manager.load()
        config2 = config_manager.load()
        
        # Should be the same instance (cached)
        assert config1 is config2

    def test_load_handles_invalid_toml(self, temp_dir: Path):
        """Test that load handles invalid TOML gracefully."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        # Write invalid TOML
        cm.config_dir.mkdir(parents=True, exist_ok=True)
        cm.config_file.write_text("invalid [[ toml")
        
        with pytest.raises(Exception):
            cm.load()

    def test_load_handles_missing_fields(self, temp_dir: Path):
        """Test that load handles missing optional fields."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        # Write minimal config
        cm.config_dir.mkdir(parents=True, exist_ok=True)
        cm.config_file.write_text('database_path = "/tmp/test.db"\n')
        
        config = cm.load()
        
        assert config.database_path == "/tmp/test.db"
        assert config.editor is None
        assert config.github_token is None


class TestConfigManagerSave:
    """Test saving configuration."""

    def test_save_writes_config_to_file(self, temp_dir: Path):
        """Test that save writes config to file."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        config = FredoConfig(
            database_path="/tmp/test.db",
            editor="nvim",
        )
        
        cm.save(config)
        
        assert cm.config_file.exists()
        content = cm.config_file.read_text()
        assert "database_path" in content
        assert "nvim" in content

    def test_save_filters_none_values(self, temp_dir: Path):
        """Test that save filters out None values."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        config = FredoConfig(
            database_path="/tmp/test.db",
            editor=None,  # Should be filtered out
            github_token=None,  # Should be filtered out
        )
        
        cm.save(config)
        
        content = cm.config_file.read_text()
        assert "database_path" in content
        # None values should not be in file
        assert "editor" not in content or "editor = " not in content
        assert "github_token" not in content or "github_token = " not in content

    def test_save_updates_cached_config(self, temp_dir: Path):
        """Test that save updates cached config."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        config1 = FredoConfig(database_path="/tmp/test1.db")
        cm.save(config1)
        
        config2 = FredoConfig(database_path="/tmp/test2.db")
        cm.save(config2)
        
        # Cached config should be updated
        assert cm._config == config2

    def test_save_creates_config_dir(self, temp_dir: Path):
        """Test that save creates config directory if needed."""
        config_dir = temp_dir / "nonexistent" / "config"
        
        cm = ConfigManager()
        cm.config_dir = config_dir
        cm.config_file = config_dir / "config.toml"
        
        config = FredoConfig(database_path="/tmp/test.db")
        cm.save(config)
        
        assert config_dir.exists()
        assert cm.config_file.exists()

    def test_save_overwrites_existing_config(self, config_manager: ConfigManager):
        """Test that save overwrites existing config."""
        original_config = config_manager.load()
        
        new_config = FredoConfig(
            database_path="/tmp/new.db",
            editor="emacs",
        )
        
        config_manager.save(new_config)
        
        # Load again to verify
        config_manager._config = None  # Clear cache
        loaded_config = config_manager.load()
        
        assert loaded_config.database_path == "/tmp/new.db"
        assert loaded_config.editor == "emacs"


class TestConfigManagerGetSet:
    """Test get/set configuration values."""

    def test_get_existing_value(self, config_manager: ConfigManager):
        """Test getting existing configuration value."""
        value = config_manager.get("editor")
        assert value == "vim"

    def test_get_none_value(self, temp_dir: Path):
        """Test getting None value."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        cm._config = FredoConfig(editor=None)
        
        value = cm.get("editor")
        assert value is None

    def test_get_nonexistent_key(self, config_manager: ConfigManager):
        """Test getting nonexistent key returns None."""
        value = config_manager.get("nonexistent_key")
        assert value is None

    def test_set_value(self, config_manager: ConfigManager):
        """Test setting configuration value."""
        config_manager.set("editor", "emacs")
        
        value = config_manager.get("editor")
        assert value == "emacs"

    def test_set_value_persists(self, config_manager: ConfigManager):
        """Test that set value persists to file."""
        config_manager.set("editor", "code")
        
        # Create new manager to load from file
        cm2 = ConfigManager()
        cm2.config_dir = config_manager.config_dir
        cm2.config_file = config_manager.config_file
        
        value = cm2.get("editor")
        assert value == "code"

    def test_set_creates_new_attribute(self, config_manager: ConfigManager):
        """Test setting new attribute (if model allows)."""
        # Note: Pydantic will allow setting existing fields only
        config_manager.set("default_execution_mode", "isolated")
        
        value = config_manager.get("default_execution_mode")
        assert value == "isolated"


class TestConfigManagerGetEditor:
    """Test get_editor functionality."""

    def test_get_editor_returns_configured_editor(
        self, config_manager: ConfigManager
    ):
        """Test that get_editor returns configured editor."""
        editor = config_manager.get_editor()
        assert editor == "vim"

    def test_get_editor_falls_back_to_visual(
        self, temp_dir: Path, monkeypatch, clean_env
    ):
        """Test that get_editor falls back to VISUAL env var."""
        monkeypatch.setenv("VISUAL", "nano")
        
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        cm._config = FredoConfig(editor=None)
        
        editor = cm.get_editor()
        assert editor == "nano"

    def test_get_editor_falls_back_to_editor(
        self, temp_dir: Path, monkeypatch, clean_env
    ):
        """Test that get_editor falls back to EDITOR env var."""
        monkeypatch.setenv("EDITOR", "emacs")
        
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        cm._config = FredoConfig(editor=None)
        
        editor = cm.get_editor()
        assert editor == "emacs"

    def test_get_editor_visual_takes_precedence_over_editor(
        self, temp_dir: Path, monkeypatch, clean_env
    ):
        """Test that VISUAL takes precedence over EDITOR."""
        monkeypatch.setenv("VISUAL", "nano")
        monkeypatch.setenv("EDITOR", "emacs")
        
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        cm._config = FredoConfig(editor=None)
        
        editor = cm.get_editor()
        assert editor == "nano"

    def test_get_editor_defaults_to_vim(
        self, temp_dir: Path, clean_env
    ):
        """Test that get_editor defaults to vim."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        cm._config = FredoConfig(editor=None)
        
        editor = cm.get_editor()
        assert editor == "vim"

    def test_get_editor_configured_overrides_env(
        self, temp_dir: Path, monkeypatch, clean_env
    ):
        """Test that configured editor overrides env vars."""
        monkeypatch.setenv("VISUAL", "nano")
        monkeypatch.setenv("EDITOR", "emacs")
        
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        cm._config = FredoConfig(editor="code")
        
        editor = cm.get_editor()
        assert editor == "code"


class TestConfigManagerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_config_with_special_characters_in_paths(self, temp_dir: Path):
        """Test config with special characters in paths."""
        db_path = temp_dir / "path with spaces" / "test.db"
        
        config = FredoConfig(database_path=str(db_path))
        
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        cm.save(config)
        loaded = cm.load()
        
        assert loaded.database_path == str(db_path)

    def test_config_with_unicode_values(self, temp_dir: Path):
        """Test config with Unicode values."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        # GitHub token could theoretically contain various chars
        config = FredoConfig(
            database_path="/tmp/test.db",
            github_token="test_世界_token",
        )
        
        cm.save(config)
        loaded = cm.load()
        
        assert loaded.github_token == "test_世界_token"

    def test_config_with_very_long_values(self, temp_dir: Path):
        """Test config with very long values."""
        long_path = "/very/" + ("long/" * 100) + "path.db"
        
        config = FredoConfig(database_path=long_path)
        
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        cm.save(config)
        loaded = cm.load()
        
        assert loaded.database_path == long_path

    def test_concurrent_config_access(self, temp_dir: Path):
        """Test that multiple config managers can access same file."""
        cm1 = ConfigManager()
        cm1.config_dir = temp_dir
        cm1.config_file = temp_dir / "config.toml"
        
        cm2 = ConfigManager()
        cm2.config_dir = temp_dir
        cm2.config_file = temp_dir / "config.toml"
        
        config = FredoConfig(database_path="/tmp/test.db")
        cm1.save(config)
        
        loaded = cm2.load()
        assert loaded.database_path == "/tmp/test.db"

    def test_config_file_permissions(self, temp_dir: Path):
        """Test that config file is created with proper permissions."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        config = FredoConfig(database_path="/tmp/test.db")
        cm.save(config)
        
        # File should be readable and writable by owner
        assert cm.config_file.exists()
        assert os.access(cm.config_file, os.R_OK)
        assert os.access(cm.config_file, os.W_OK)


class TestConfigManagerGlobalInstance:
    """Test the global config manager instance."""

    def test_global_config_manager_exists(self):
        """Test that global config manager exists."""
        from fredo.utils.config import config_manager
        
        assert config_manager is not None
        assert isinstance(config_manager, ConfigManager)

    def test_global_config_manager_is_functional(self):
        """Test that global config manager works."""
        from fredo.utils.config import config_manager
        
        # Should be able to load (creates default if needed)
        config = config_manager.load()
        
        assert isinstance(config, FredoConfig)


class TestConfigManagerIntegration:
    """Test ConfigManager integration scenarios."""

    def test_complete_workflow(self, temp_dir: Path):
        """Test complete config workflow."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        # 1. Load (creates default)
        config = cm.load()
        assert config is not None
        
        # 2. Modify and save
        cm.set("editor", "nvim")
        cm.set("github_token", "new_token")
        
        # 3. Load again in new manager
        cm2 = ConfigManager()
        cm2.config_dir = temp_dir
        cm2.config_file = temp_dir / "config.toml"
        
        config2 = cm2.load()
        assert config2.editor == "nvim"
        assert config2.github_token == "new_token"

    def test_migration_scenario(self, temp_dir: Path):
        """Test migrating from old to new config format."""
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        
        # Write old format config (missing new fields)
        cm.config_dir.mkdir(parents=True, exist_ok=True)
        cm.config_file.write_text('database_path = "/old/path.db"\n')
        
        # Load should work and add defaults for missing fields
        config = cm.load()
        
        assert config.database_path == "/old/path.db"
        assert config.default_execution_mode == "current"  # Default value
        assert config.gist_private_by_default is True  # Default value

