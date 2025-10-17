"""Tests for the Snippet model."""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from fredo.core.models import Snippet


class TestSnippetCreation:
    """Test snippet creation and validation."""

    def test_create_snippet_with_required_fields(self):
        """Test creating a snippet with only required fields."""
        snippet = Snippet(name="test", content="print('hello')")
        
        assert snippet.name == "test"
        assert snippet.content == "print('hello')"
        assert snippet.language == "auto"
        assert snippet.tags == []
        assert snippet.execution_mode == "current"
        assert snippet.gist_id is None
        assert snippet.gist_url is None
        assert isinstance(snippet.id, str)
        assert len(snippet.id) > 0
        assert isinstance(snippet.created_at, datetime)
        assert isinstance(snippet.updated_at, datetime)

    def test_create_snippet_with_all_fields(self):
        """Test creating a snippet with all fields."""
        created = datetime(2024, 1, 1, 12, 0, 0)
        updated = datetime(2024, 1, 2, 12, 0, 0)
        
        snippet = Snippet(
            id="custom-id",
            name="full-snippet",
            content="#!/bin/bash\necho 'test'",
            language="bash",
            tags=["shell", "test"],
            execution_mode="isolated",
            gist_id="gist123",
            gist_url="https://gist.github.com/user/gist123",
            created_at=created,
            updated_at=updated,
        )
        
        assert snippet.id == "custom-id"
        assert snippet.name == "full-snippet"
        assert snippet.content == "#!/bin/bash\necho 'test'"
        assert snippet.language == "bash"
        assert snippet.tags == ["shell", "test"]
        assert snippet.execution_mode == "isolated"
        assert snippet.gist_id == "gist123"
        assert snippet.gist_url == "https://gist.github.com/user/gist123"
        assert snippet.created_at == created
        assert snippet.updated_at == updated

    def test_snippet_generates_unique_ids(self):
        """Test that snippets generate unique IDs."""
        snippet1 = Snippet(name="test1", content="content1")
        snippet2 = Snippet(name="test2", content="content2")
        
        assert snippet1.id != snippet2.id
        assert len(snippet1.id) > 0
        assert len(snippet2.id) > 0


class TestSnippetValidation:
    """Test snippet validation."""

    def test_empty_name_raises_error(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Snippet(name="", content="test")
        
        assert "name" in str(exc_info.value)

    def test_missing_name_raises_error(self):
        """Test that missing name raises validation error."""
        with pytest.raises(ValidationError):
            Snippet(content="test")

    def test_empty_content_raises_error(self):
        """Test that empty content raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Snippet(name="test", content="")
        
        assert "content" in str(exc_info.value)

    def test_missing_content_raises_error(self):
        """Test that missing content raises validation error."""
        with pytest.raises(ValidationError):
            Snippet(name="test")

    def test_very_long_name_raises_error(self):
        """Test that names longer than 255 characters raise error."""
        long_name = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            Snippet(name=long_name, content="test")
        
        assert "name" in str(exc_info.value)

    def test_name_exactly_255_chars_is_valid(self):
        """Test that names exactly 255 characters are valid."""
        name_255 = "a" * 255
        snippet = Snippet(name=name_255, content="test")
        assert snippet.name == name_255

    def test_invalid_execution_mode_raises_error(self):
        """Test that invalid execution mode raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Snippet(name="test", content="test", execution_mode="invalid")
        
        assert "execution_mode" in str(exc_info.value)

    def test_valid_execution_modes(self):
        """Test that valid execution modes are accepted."""
        snippet1 = Snippet(name="test1", content="test", execution_mode="current")
        snippet2 = Snippet(name="test2", content="test", execution_mode="isolated")
        
        assert snippet1.execution_mode == "current"
        assert snippet2.execution_mode == "isolated"


class TestSnippetTags:
    """Test tag validation and processing."""

    def test_tags_are_normalized_to_lowercase(self):
        """Test that tags are converted to lowercase."""
        snippet = Snippet(
            name="test",
            content="test",
            tags=["Python", "BASH", "Test"],
        )
        
        assert snippet.tags == ["python", "bash", "test"]

    def test_tags_are_stripped(self):
        """Test that tags are stripped of whitespace."""
        snippet = Snippet(
            name="test",
            content="test",
            tags=["  python  ", "bash", "  test"],
        )
        
        assert snippet.tags == ["python", "bash", "test"]

    def test_empty_tags_are_filtered(self):
        """Test that empty tags are filtered out."""
        snippet = Snippet(
            name="test",
            content="test",
            tags=["python", "", "  ", "bash"],
        )
        
        assert snippet.tags == ["python", "bash"]

    def test_empty_tags_list(self):
        """Test that empty tags list is handled correctly."""
        snippet = Snippet(name="test", content="test", tags=[])
        assert snippet.tags == []

    def test_tags_with_special_characters(self):
        """Test that tags with special characters are preserved."""
        snippet = Snippet(
            name="test",
            content="test",
            tags=["python-3", "node.js", "c++"],
        )
        
        # Should be lowercase but preserve special chars
        assert snippet.tags == ["python-3", "node.js", "c++"]


class TestSnippetSerialization:
    """Test snippet serialization to and from database format."""

    def test_to_db_dict(self):
        """Test converting snippet to database dictionary."""
        created = datetime(2024, 1, 1, 12, 0, 0)
        updated = datetime(2024, 1, 2, 12, 0, 0)
        
        snippet = Snippet(
            id="test-id",
            name="test-snippet",
            content="print('hello')",
            language="python",
            tags=["test", "example"],
            execution_mode="isolated",
            gist_id="gist123",
            gist_url="https://gist.github.com/user/gist123",
            created_at=created,
            updated_at=updated,
        )
        
        db_dict = snippet.to_db_dict()
        
        assert db_dict["id"] == "test-id"
        assert db_dict["name"] == "test-snippet"
        assert db_dict["content"] == "print('hello')"
        assert db_dict["language"] == "python"
        assert db_dict["tags"] == '["test", "example"]'
        assert db_dict["execution_mode"] == "isolated"
        assert db_dict["gist_id"] == "gist123"
        assert db_dict["gist_url"] == "https://gist.github.com/user/gist123"
        assert db_dict["created_at"] == created.isoformat()
        assert db_dict["updated_at"] == updated.isoformat()

    def test_to_db_dict_with_empty_tags(self):
        """Test converting snippet with empty tags."""
        snippet = Snippet(name="test", content="test", tags=[])
        db_dict = snippet.to_db_dict()
        assert db_dict["tags"] == "[]"

    def test_to_db_dict_with_null_gist_fields(self):
        """Test converting snippet with null Gist fields."""
        snippet = Snippet(name="test", content="test")
        db_dict = snippet.to_db_dict()
        assert db_dict["gist_id"] is None
        assert db_dict["gist_url"] is None

    def test_from_db_dict(self):
        """Test creating snippet from database dictionary."""
        db_dict = {
            "id": "test-id",
            "name": "test-snippet",
            "content": "print('hello')",
            "language": "python",
            "tags": '["test", "example"]',
            "execution_mode": "isolated",
            "gist_id": "gist123",
            "gist_url": "https://gist.github.com/user/gist123",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-02T12:00:00",
        }
        
        snippet = Snippet.from_db_dict(db_dict)
        
        assert snippet.id == "test-id"
        assert snippet.name == "test-snippet"
        assert snippet.content == "print('hello')"
        assert snippet.language == "python"
        assert snippet.tags == ["test", "example"]
        assert snippet.execution_mode == "isolated"
        assert snippet.gist_id == "gist123"
        assert snippet.gist_url == "https://gist.github.com/user/gist123"
        assert snippet.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert snippet.updated_at == datetime(2024, 1, 2, 12, 0, 0)

    def test_from_db_dict_with_empty_tags(self):
        """Test creating snippet from dict with empty tags."""
        db_dict = {
            "id": "test-id",
            "name": "test",
            "content": "test",
            "language": "auto",
            "tags": "[]",
            "execution_mode": "current",
            "gist_id": None,
            "gist_url": None,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        }
        
        snippet = Snippet.from_db_dict(db_dict)
        assert snippet.tags == []

    def test_from_db_dict_with_null_tags(self):
        """Test creating snippet from dict with null tags."""
        db_dict = {
            "id": "test-id",
            "name": "test",
            "content": "test",
            "language": "auto",
            "tags": None,
            "execution_mode": "current",
            "gist_id": None,
            "gist_url": None,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        }
        
        snippet = Snippet.from_db_dict(db_dict)
        assert snippet.tags == []

    def test_roundtrip_serialization(self):
        """Test that snippet can be serialized and deserialized."""
        original = Snippet(
            name="test",
            content="print('test')",
            language="python",
            tags=["test", "example"],
            execution_mode="isolated",
        )
        
        db_dict = original.to_db_dict()
        restored = Snippet.from_db_dict(db_dict)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.content == original.content
        assert restored.language == original.language
        assert restored.tags == original.tags
        assert restored.execution_mode == original.execution_mode


class TestSnippetFileExtension:
    """Test file extension detection."""

    def test_get_python_extension(self):
        """Test getting .py extension for Python."""
        snippet = Snippet(name="test", content="test", language="python")
        assert snippet.get_file_extension() == ".py"

    def test_get_bash_extension(self):
        """Test getting .sh extension for bash."""
        snippet = Snippet(name="test", content="test", language="bash")
        assert snippet.get_file_extension() == ".sh"

    def test_get_shell_extension(self):
        """Test getting .sh extension for shell."""
        snippet = Snippet(name="test", content="test", language="shell")
        assert snippet.get_file_extension() == ".sh"

    def test_get_javascript_extension(self):
        """Test getting .js extension for JavaScript."""
        snippet = Snippet(name="test", content="test", language="javascript")
        assert snippet.get_file_extension() == ".js"

    def test_get_typescript_extension(self):
        """Test getting .ts extension for TypeScript."""
        snippet = Snippet(name="test", content="test", language="typescript")
        assert snippet.get_file_extension() == ".ts"

    def test_get_ruby_extension(self):
        """Test getting .rb extension for Ruby."""
        snippet = Snippet(name="test", content="test", language="ruby")
        assert snippet.get_file_extension() == ".rb"

    def test_get_go_extension(self):
        """Test getting .go extension for Go."""
        snippet = Snippet(name="test", content="test", language="go")
        assert snippet.get_file_extension() == ".go"

    def test_get_rust_extension(self):
        """Test getting .rs extension for Rust."""
        snippet = Snippet(name="test", content="test", language="rust")
        assert snippet.get_file_extension() == ".rs"

    def test_get_extension_case_insensitive(self):
        """Test that language detection is case-insensitive."""
        snippet1 = Snippet(name="test", content="test", language="Python")
        snippet2 = Snippet(name="test", content="test", language="PYTHON")
        
        assert snippet1.get_file_extension() == ".py"
        assert snippet2.get_file_extension() == ".py"

    def test_get_unknown_extension_returns_txt(self):
        """Test that unknown languages return .txt."""
        snippet = Snippet(name="test", content="test", language="unknown")
        assert snippet.get_file_extension() == ".txt"

    def test_get_auto_extension_returns_txt(self):
        """Test that 'auto' language returns .txt."""
        snippet = Snippet(name="test", content="test", language="auto")
        assert snippet.get_file_extension() == ".txt"

    def test_all_supported_extensions(self):
        """Test all supported file extensions."""
        test_cases = [
            ("python", ".py"),
            ("bash", ".sh"),
            ("javascript", ".js"),
            ("typescript", ".ts"),
            ("ruby", ".rb"),
            ("go", ".go"),
            ("rust", ".rs"),
            ("java", ".java"),
            ("c", ".c"),
            ("cpp", ".cpp"),
            ("csharp", ".cs"),
            ("php", ".php"),
            ("sql", ".sql"),
            ("html", ".html"),
            ("css", ".css"),
            ("json", ".json"),
            ("yaml", ".yaml"),
            ("markdown", ".md"),
        ]
        
        for language, expected_ext in test_cases:
            snippet = Snippet(name="test", content="test", language=language)
            assert snippet.get_file_extension() == expected_ext, \
                f"Language {language} should have extension {expected_ext}"


class TestSnippetEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_snippet_with_unicode_content(self):
        """Test snippet with Unicode characters in content."""
        snippet = Snippet(
            name="unicode-test",
            content="print('Hello 世界 🌍')",
        )
        
        assert snippet.content == "print('Hello 世界 🌍')"

    def test_snippet_with_unicode_name(self):
        """Test snippet with Unicode characters in name."""
        snippet = Snippet(
            name="test-世界",
            content="test",
        )
        
        assert snippet.name == "test-世界"

    def test_snippet_with_unicode_tags(self):
        """Test snippet with Unicode characters in tags."""
        snippet = Snippet(
            name="test",
            content="test",
            tags=["test-世界", "emoji-🚀"],
        )
        
        assert "test-世界" in snippet.tags
        assert "emoji-🚀" in snippet.tags

    def test_snippet_with_multiline_content(self):
        """Test snippet with multiline content."""
        content = """#!/usr/bin/env python3
import sys

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
"""
        snippet = Snippet(name="multiline", content=content)
        assert snippet.content == content

    def test_snippet_with_special_chars_in_name(self):
        """Test snippet with special characters in name."""
        snippet = Snippet(
            name="test-snippet_v1.0",
            content="test",
        )
        
        assert snippet.name == "test-snippet_v1.0"

    def test_snippet_with_very_long_content(self):
        """Test snippet with very long content."""
        long_content = "x" * 100000
        snippet = Snippet(name="long", content=long_content)
        
        assert len(snippet.content) == 100000
        assert snippet.content == long_content

    def test_snippet_with_null_bytes_in_content(self):
        """Test snippet with null bytes (edge case)."""
        # Null bytes should be preserved
        snippet = Snippet(name="test", content="test\x00content")
        assert "\x00" in snippet.content

