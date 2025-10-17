"""Configuration management for Fredo."""

import os
import sys
from pathlib import Path
from typing import Optional

import tomli_w
from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class FredoConfig(BaseModel):
    """Configuration model for Fredo."""

    database_path: str = Field(
        default_factory=lambda: str(
            Path.home() / ".local" / "share" / "fredo" / "snippets.db"
        )
    )
    editor: Optional[str] = None
    github_token: Optional[str] = None
    default_execution_mode: str = Field(default="current")
    gist_private_by_default: bool = Field(default=True)

    class Config:
        """Pydantic config."""

        validate_assignment = True


class ConfigManager:
    """Manages Fredo configuration."""

    def __init__(self):
        """Initialize the config manager."""
        self.config_dir = Path.home() / ".config" / "fredo"
        self.config_file = self.config_dir / "config.toml"
        self._config: Optional[FredoConfig] = None

    def ensure_config_dir(self):
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def ensure_data_dir(self):
        """Ensure data directory exists."""
        data_dir = Path.home() / ".local" / "share" / "fredo"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def load(self) -> FredoConfig:
        """Load configuration from file or create default."""
        if self._config is not None:
            return self._config

        self.ensure_config_dir()

        if self.config_file.exists():
            with open(self.config_file, "rb") as f:
                data = tomllib.load(f)
                self._config = FredoConfig(**data)
        else:
            # Create default config
            self._config = FredoConfig()
            self.save(self._config)

        return self._config

    def save(self, config: FredoConfig):
        """Save configuration to file."""
        self.ensure_config_dir()
        # Filter out None values for TOML serialization
        data = {k: v for k, v in config.model_dump().items() if v is not None}
        with open(self.config_file, "wb") as f:
            tomli_w.dump(data, f)
        self._config = config

    def get(self, key: str) -> Optional[str]:
        """Get a configuration value."""
        config = self.load()
        return getattr(config, key, None)

    def set(self, key: str, value: str):
        """Set a configuration value."""
        config = self.load()
        setattr(config, key, value)
        self.save(config)

    def get_editor(self) -> str:
        """Get the editor to use."""
        config = self.load()
        if config.editor:
            return config.editor
        return os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vim"


# Global config manager instance
config_manager = ConfigManager()

