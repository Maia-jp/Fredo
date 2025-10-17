"""Tests for the Database operations."""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from fredo.core.database import Database
from fredo.core.models import Snippet


class TestDatabaseInitialization:
    """Test database initialization."""

    def test_init_db_creates_table(self, temp_db_path: Path):
        """Test that init_db creates the snippets table."""
        db = Database()
        db.db_path = temp_db_path
        db.init_db()
        
        # Verify table exists
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='snippets'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_init_db_creates_indexes(self, temp_db_path: Path):
        """Test that init_db creates indexes."""
        db = Database()
        db.db_path = temp_db_path
        db.init_db()
        
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name IN ('idx_name', 'idx_language')"
            )
            indexes = cursor.fetchall()
            assert len(indexes) == 2

    def test_init_db_is_idempotent(self, temp_db_path: Path):
        """Test that calling init_db multiple times is safe."""
        db = Database()
        db.db_path = temp_db_path
        
        # Call multiple times
        db.init_db()
        db.init_db()
        db.init_db()
        
        # Should still work
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM snippets")
            count = cursor.fetchone()[0]
            assert count == 0

    def test_db_path_is_created(self, temp_dir: Path, config_manager):
        """Test that database directory is created if it doesn't exist."""
        db_path = temp_dir / "nonexistent" / "path" / "snippets.db"
        
        db = Database()
        db.db_path = db_path
        db.init_db()
        
        assert db_path.exists()
        assert db_path.parent.exists()


class TestDatabaseCreate:
    """Test creating snippets."""

    def test_create_snippet(self, db: Database, sample_snippet: Snippet):
        """Test creating a new snippet."""
        result = db.create(sample_snippet)
        
        assert result.id == sample_snippet.id
        assert result.name == sample_snippet.name
        assert result.content == sample_snippet.content

    def test_create_snippet_persists_to_database(
        self, db: Database, sample_snippet: Snippet
    ):
        """Test that created snippet is persisted."""
        db.create(sample_snippet)
        
        # Verify in database
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snippets WHERE id = ?", (sample_snippet.id,)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row["name"] == sample_snippet.name

    def test_create_duplicate_name_raises_error(
        self, db: Database, sample_snippet: Snippet
    ):
        """Test that creating duplicate name raises error."""
        db.create(sample_snippet)
        
        duplicate = Snippet(name=sample_snippet.name, content="different content")
        
        with pytest.raises(sqlite3.IntegrityError):
            db.create(duplicate)

    def test_create_snippet_with_all_fields(self, db: Database):
        """Test creating snippet with all fields populated."""
        snippet = Snippet(
            name="full-snippet",
            content="test content",
            language="python",
            tags=["test", "example"],
            execution_mode="isolated",
            gist_id="gist123",
            gist_url="https://gist.github.com/user/gist123",
        )
        
        result = db.create(snippet)
        
        # Verify all fields
        retrieved = db.get_by_id(result.id)
        assert retrieved.name == "full-snippet"
        assert retrieved.content == "test content"
        assert retrieved.language == "python"
        assert retrieved.tags == ["test", "example"]
        assert retrieved.execution_mode == "isolated"
        assert retrieved.gist_id == "gist123"
        assert retrieved.gist_url == "https://gist.github.com/user/gist123"

    def test_create_multiple_snippets(self, db: Database, multiple_snippets):
        """Test creating multiple snippets."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        all_snippets = db.list_all()
        assert len(all_snippets) == len(multiple_snippets)


class TestDatabaseRead:
    """Test reading snippets."""

    def test_get_by_id_existing_snippet(self, db: Database, sample_snippet: Snippet):
        """Test getting snippet by ID."""
        db.create(sample_snippet)
        
        result = db.get_by_id(sample_snippet.id)
        
        assert result is not None
        assert result.id == sample_snippet.id
        assert result.name == sample_snippet.name
        assert result.content == sample_snippet.content

    def test_get_by_id_nonexistent_snippet(self, db: Database):
        """Test getting nonexistent snippet returns None."""
        result = db.get_by_id("nonexistent-id")
        assert result is None

    def test_get_by_name_existing_snippet(
        self, db: Database, sample_snippet: Snippet
    ):
        """Test getting snippet by name."""
        db.create(sample_snippet)
        
        result = db.get_by_name(sample_snippet.name)
        
        assert result is not None
        assert result.name == sample_snippet.name
        assert result.id == sample_snippet.id

    def test_get_by_name_nonexistent_snippet(self, db: Database):
        """Test getting nonexistent snippet by name returns None."""
        result = db.get_by_name("nonexistent-name")
        assert result is None

    def test_get_by_name_case_sensitive(self, db: Database, sample_snippet: Snippet):
        """Test that get_by_name is case-sensitive."""
        db.create(sample_snippet)
        
        result = db.get_by_name(sample_snippet.name.upper())
        assert result is None

    def test_list_all_empty_database(self, db: Database):
        """Test listing all snippets in empty database."""
        result = db.list_all()
        assert result == []

    def test_list_all_returns_all_snippets(self, db: Database, multiple_snippets):
        """Test that list_all returns all snippets."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.list_all()
        
        assert len(result) == len(multiple_snippets)
        result_names = [s.name for s in result]
        for snippet in multiple_snippets:
            assert snippet.name in result_names

    def test_list_all_sorted_by_updated_at_desc(self, db: Database):
        """Test that list_all returns snippets sorted by updated_at descending."""
        snippet1 = Snippet(
            name="old",
            content="test",
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        snippet2 = Snippet(
            name="new",
            content="test",
            updated_at=datetime(2024, 1, 2, 12, 0, 0),
        )
        
        db.create(snippet1)
        db.create(snippet2)
        
        result = db.list_all()
        
        # Newest first
        assert result[0].name == "new"
        assert result[1].name == "old"


class TestDatabaseUpdate:
    """Test updating snippets."""

    def test_update_snippet_content(self, db: Database, sample_snippet: Snippet):
        """Test updating snippet content."""
        db.create(sample_snippet)
        
        sample_snippet.content = "updated content"
        db.update(sample_snippet)
        
        result = db.get_by_id(sample_snippet.id)
        assert result.content == "updated content"

    def test_update_snippet_name(self, db: Database, sample_snippet: Snippet):
        """Test updating snippet name."""
        db.create(sample_snippet)
        
        sample_snippet.name = "new-name"
        db.update(sample_snippet)
        
        result = db.get_by_id(sample_snippet.id)
        assert result.name == "new-name"
        
        # Old name should not exist
        old_result = db.get_by_name("test-snippet")
        assert old_result is None

    def test_update_snippet_tags(self, db: Database, sample_snippet: Snippet):
        """Test updating snippet tags."""
        db.create(sample_snippet)
        
        sample_snippet.tags = ["new", "tags"]
        db.update(sample_snippet)
        
        result = db.get_by_id(sample_snippet.id)
        assert result.tags == ["new", "tags"]

    def test_update_snippet_gist_info(self, db: Database, sample_snippet: Snippet):
        """Test updating snippet Gist information."""
        db.create(sample_snippet)
        
        sample_snippet.gist_id = "new_gist_id"
        sample_snippet.gist_url = "https://gist.github.com/user/new_gist_id"
        db.update(sample_snippet)
        
        result = db.get_by_id(sample_snippet.id)
        assert result.gist_id == "new_gist_id"
        assert result.gist_url == "https://gist.github.com/user/new_gist_id"

    def test_update_updates_timestamp(self, db: Database, sample_snippet: Snippet):
        """Test that update updates the updated_at timestamp."""
        db.create(sample_snippet)
        original_updated = sample_snippet.updated_at
        
        # Wait a tiny bit and update
        sample_snippet.content = "updated"
        db.update(sample_snippet)
        
        result = db.get_by_id(sample_snippet.id)
        # updated_at should be set by update() method
        assert result.updated_at >= original_updated

    def test_update_nonexistent_snippet_does_nothing(self, db: Database):
        """Test that updating nonexistent snippet doesn't raise error."""
        snippet = Snippet(id="nonexistent", name="test", content="test")
        
        # Should not raise error
        db.update(snippet)
        
        # Should not exist
        result = db.get_by_id("nonexistent")
        assert result is None


class TestDatabaseDelete:
    """Test deleting snippets."""

    def test_delete_by_id_existing_snippet(
        self, db: Database, sample_snippet: Snippet
    ):
        """Test deleting snippet by ID."""
        db.create(sample_snippet)
        
        result = db.delete(sample_snippet.id)
        
        assert result is True
        assert db.get_by_id(sample_snippet.id) is None

    def test_delete_by_id_nonexistent_snippet(self, db: Database):
        """Test deleting nonexistent snippet returns False."""
        result = db.delete("nonexistent-id")
        assert result is False

    def test_delete_by_name_existing_snippet(
        self, db: Database, sample_snippet: Snippet
    ):
        """Test deleting snippet by name."""
        db.create(sample_snippet)
        
        result = db.delete_by_name(sample_snippet.name)
        
        assert result is True
        assert db.get_by_name(sample_snippet.name) is None

    def test_delete_by_name_nonexistent_snippet(self, db: Database):
        """Test deleting nonexistent snippet by name returns False."""
        result = db.delete_by_name("nonexistent-name")
        assert result is False

    def test_delete_is_permanent(self, db: Database, sample_snippet: Snippet):
        """Test that deletion is permanent."""
        db.create(sample_snippet)
        db.delete(sample_snippet.id)
        
        # Try to get it again
        result = db.get_by_id(sample_snippet.id)
        assert result is None
        
        # List all should not include it
        all_snippets = db.list_all()
        assert len(all_snippets) == 0


class TestDatabaseSearch:
    """Test searching snippets."""

    def test_search_no_filters(self, db: Database, multiple_snippets):
        """Test search with no filters returns all snippets."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.search()
        
        assert len(result) == len(multiple_snippets)

    def test_search_by_query_in_name(self, db: Database, multiple_snippets):
        """Test searching by query matching name."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.search(query="python")
        
        assert len(result) == 2
        result_names = [s.name for s in result]
        assert "python-hello" in result_names
        assert "python-calc" in result_names

    def test_search_by_query_in_content(self, db: Database, multiple_snippets):
        """Test searching by query matching content."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.search(query="docker")
        
        assert len(result) == 1
        assert result[0].name == "docker-cleanup"

    def test_search_by_query_case_insensitive(self, db: Database, multiple_snippets):
        """Test that search is case-insensitive."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.search(query="PYTHON")
        
        assert len(result) == 2

    def test_search_by_language(self, db: Database, multiple_snippets):
        """Test searching by language filter."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.search(language="python")
        
        assert len(result) == 2
        for snippet in result:
            assert snippet.language == "python"

    def test_search_by_single_tag(self, db: Database, multiple_snippets):
        """Test searching by single tag."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.search(tags=["hello"])
        
        assert len(result) == 2
        result_names = [s.name for s in result]
        assert "python-hello" in result_names
        assert "bash-script" in result_names

    def test_search_by_multiple_tags_or(self, db: Database, multiple_snippets):
        """Test searching with multiple tags (OR logic)."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.search(tags=["docker", "api"])
        
        # Should match snippets with docker OR api
        assert len(result) == 2
        result_names = [s.name for s in result]
        assert "docker-cleanup" in result_names
        assert "js-fetch" in result_names

    def test_search_combined_filters(self, db: Database, multiple_snippets):
        """Test searching with combined filters."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.search(query="hello", language="python")
        
        assert len(result) == 1
        assert result[0].name == "python-hello"

    def test_search_no_results(self, db: Database, multiple_snippets):
        """Test search with no matching results."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.search(query="nonexistent")
        
        assert len(result) == 0

    def test_search_empty_database(self, db: Database):
        """Test searching empty database."""
        result = db.search(query="anything")
        assert len(result) == 0

    def test_search_partial_match(self, db: Database):
        """Test search with partial query match."""
        snippet = Snippet(name="test-docker-compose", content="docker compose up")
        db.create(snippet)
        
        result = db.search(query="dock")
        
        assert len(result) == 1
        assert result[0].name == "test-docker-compose"


class TestDatabaseGetAllTags:
    """Test getting all tags."""

    def test_get_all_tags_empty_database(self, db: Database):
        """Test getting tags from empty database."""
        result = db.get_all_tags()
        assert result == []

    def test_get_all_tags_with_snippets(self, db: Database, multiple_snippets):
        """Test getting all tags with counts."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.get_all_tags()
        
        # Convert to dict for easier assertion
        tag_dict = dict(result)
        
        assert "python" in tag_dict
        assert tag_dict["python"] == 2
        assert "hello" in tag_dict
        assert tag_dict["hello"] == 2
        assert "docker" in tag_dict
        assert tag_dict["docker"] == 1

    def test_get_all_tags_sorted_by_count_desc(self, db: Database, multiple_snippets):
        """Test that tags are sorted by count descending."""
        for snippet in multiple_snippets:
            db.create(snippet)
        
        result = db.get_all_tags()
        
        # Should be sorted by count
        counts = [count for _, count in result]
        assert counts == sorted(counts, reverse=True)

    def test_get_all_tags_excludes_empty_tags(self, db: Database):
        """Test that snippets with no tags are excluded."""
        snippet = Snippet(name="no-tags", content="test", tags=[])
        db.create(snippet)
        
        result = db.get_all_tags()
        
        assert result == []

    def test_get_all_tags_duplicates_counted(self, db: Database):
        """Test that duplicate tags are properly counted."""
        snippet1 = Snippet(name="s1", content="test", tags=["common", "unique1"])
        snippet2 = Snippet(name="s2", content="test", tags=["common", "unique2"])
        snippet3 = Snippet(name="s3", content="test", tags=["common"])
        
        db.create(snippet1)
        db.create(snippet2)
        db.create(snippet3)
        
        result = db.get_all_tags()
        tag_dict = dict(result)
        
        assert tag_dict["common"] == 3
        assert tag_dict["unique1"] == 1
        assert tag_dict["unique2"] == 1


class TestDatabaseTransactions:
    """Test database transaction behavior."""

    def test_connection_commits_on_success(self, db: Database, sample_snippet: Snippet):
        """Test that connection commits on success."""
        with db.get_connection() as conn:
            data = sample_snippet.to_db_dict()
            conn.execute(
                "INSERT INTO snippets (id, name, content, language, tags, "
                "execution_mode, gist_id, gist_url, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data["id"], data["name"], data["content"], data["language"],
                    data["tags"], data["execution_mode"], data["gist_id"],
                    data["gist_url"], data["created_at"], data["updated_at"],
                ),
            )
        
        # Should be committed
        result = db.get_by_id(sample_snippet.id)
        assert result is not None

    def test_connection_rolls_back_on_error(self, db: Database, sample_snippet: Snippet):
        """Test that connection rolls back on error."""
        db.create(sample_snippet)
        
        try:
            with db.get_connection() as conn:
                # Try to insert duplicate
                data = sample_snippet.to_db_dict()
                conn.execute(
                    "INSERT INTO snippets (id, name, content, language, tags, "
                    "execution_mode, gist_id, gist_url, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        data["id"], data["name"], data["content"], data["language"],
                        data["tags"], data["execution_mode"], data["gist_id"],
                        data["gist_url"], data["created_at"], data["updated_at"],
                    ),
                )
        except sqlite3.IntegrityError:
            pass
        
        # Original should still be there
        result = db.get_by_id(sample_snippet.id)
        assert result is not None


class TestDatabaseEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_snippet_with_quotes_in_content(self, db: Database):
        """Test snippet with quotes in content."""
        snippet = Snippet(
            name="quotes-test",
            content='print("Hello \'World\'")',
        )
        db.create(snippet)
        
        result = db.get_by_name("quotes-test")
        assert result.content == 'print("Hello \'World\'")'

    def test_snippet_with_sql_injection_attempt(self, db: Database):
        """Test that SQL injection is prevented."""
        snippet = Snippet(
            name="sql-injection",
            content="'; DROP TABLE snippets; --",
        )
        db.create(snippet)
        
        result = db.get_by_name("sql-injection")
        assert result is not None
        
        # Table should still exist
        all_snippets = db.list_all()
        assert len(all_snippets) == 1

    def test_snippet_with_very_long_content(self, db: Database):
        """Test snippet with very long content."""
        long_content = "x" * 1000000  # 1MB of content
        snippet = Snippet(name="long-content", content=long_content)
        
        db.create(snippet)
        result = db.get_by_name("long-content")
        
        assert len(result.content) == 1000000

    def test_concurrent_access_same_snippet(self, db: Database, sample_snippet: Snippet):
        """Test concurrent access to same snippet."""
        db.create(sample_snippet)
        
        # Both reads should succeed
        result1 = db.get_by_id(sample_snippet.id)
        result2 = db.get_by_id(sample_snippet.id)
        
        assert result1 is not None
        assert result2 is not None
        assert result1.id == result2.id

