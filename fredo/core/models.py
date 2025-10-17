"""Data models for Fredo."""

import json
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class Snippet(BaseModel):
    """Model for a code snippet."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    language: str = Field(default="auto")
    tags: List[str] = Field(default_factory=list)
    execution_mode: str = Field(default="current")
    gist_id: Optional[str] = None
    gist_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("execution_mode")
    @classmethod
    def validate_execution_mode(cls, v: str) -> str:
        """Validate execution mode."""
        if v not in ["current", "isolated"]:
            raise ValueError("execution_mode must be 'current' or 'isolated'")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean tags."""
        return [tag.strip().lower() for tag in v if tag.strip()]

    def to_db_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "language": self.language,
            "tags": json.dumps(self.tags),
            "execution_mode": self.execution_mode,
            "gist_id": self.gist_id,
            "gist_url": self.gist_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_db_dict(cls, data: dict) -> "Snippet":
        """Create snippet from database dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            content=data["content"],
            language=data["language"],
            tags=json.loads(data["tags"]) if data["tags"] else [],
            execution_mode=data["execution_mode"],
            gist_id=data.get("gist_id"),
            gist_url=data.get("gist_url"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def get_file_extension(self) -> str:
        """Get appropriate file extension for the snippet's language."""
        return get_file_extension_for_language(self.language)


def get_file_extension_for_language(language: str) -> str:
    """Get appropriate file extension for a language."""
    extension_map = {
        "python": ".py",
        "bash": ".sh",
        "shell": ".sh",
        "javascript": ".js",
        "typescript": ".ts",
        "ruby": ".rb",
        "go": ".go",
        "rust": ".rs",
        "java": ".java",
        "c": ".c",
        "cpp": ".cpp",
        "csharp": ".cs",
        "php": ".php",
        "sql": ".sql",
        "html": ".html",
        "css": ".css",
        "json": ".json",
        "yaml": ".yaml",
        "markdown": ".md",
    }
    return extension_map.get(language.lower(), ".txt")

