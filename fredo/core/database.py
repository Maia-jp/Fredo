"""Database operations for Fredo."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fredo.core.models import Snippet
from fredo.utils.config import config_manager


class Database:
    """Database manager for snippets."""

    def __init__(self):
        """Initialize the database."""
        self.db_path = None

    def _get_db_path(self) -> Path:
        """Get the database path from config."""
        if self.db_path is None:
            config = config_manager.load()
            self.db_path = Path(config.database_path)
        # Always ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return self.db_path

    @contextmanager
    def get_connection(self):
        """Get a database connection with context manager."""
        db_path = self._get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        """Initialize the database schema."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snippets (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    language TEXT NOT NULL,
                    tags TEXT,
                    execution_mode TEXT DEFAULT 'current',
                    gist_id TEXT,
                    gist_url TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            # Create indexes for better search performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_name ON snippets(name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_language ON snippets(language)"
            )

    def create(self, snippet: Snippet) -> Snippet:
        """Create a new snippet."""
        self.init_db()
        with self.get_connection() as conn:
            data = snippet.to_db_dict()
            conn.execute(
                """
                INSERT INTO snippets 
                (id, name, content, language, tags, execution_mode, 
                 gist_id, gist_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["name"],
                    data["content"],
                    data["language"],
                    data["tags"],
                    data["execution_mode"],
                    data["gist_id"],
                    data["gist_url"],
                    data["created_at"],
                    data["updated_at"],
                ),
            )
        return snippet

    def get_by_id(self, snippet_id: str) -> Optional[Snippet]:
        """Get a snippet by ID."""
        self.init_db()
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snippets WHERE id = ?", (snippet_id,)
            )
            row = cursor.fetchone()
            if row:
                return Snippet.from_db_dict(dict(row))
            return None

    def get_by_name(self, name: str) -> Optional[Snippet]:
        """Get a snippet by name."""
        self.init_db()
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snippets WHERE name = ?", (name,)
            )
            row = cursor.fetchone()
            if row:
                return Snippet.from_db_dict(dict(row))
            return None

    def update(self, snippet: Snippet) -> Snippet:
        """Update an existing snippet."""
        snippet.updated_at = datetime.now()
        data = snippet.to_db_dict()
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE snippets 
                SET name = ?, content = ?, language = ?, tags = ?,
                    execution_mode = ?, gist_id = ?, gist_url = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    data["name"],
                    data["content"],
                    data["language"],
                    data["tags"],
                    data["execution_mode"],
                    data["gist_id"],
                    data["gist_url"],
                    data["updated_at"],
                    data["id"],
                ),
            )
        return snippet

    def delete(self, snippet_id: str) -> bool:
        """Delete a snippet by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM snippets WHERE id = ?", (snippet_id,)
            )
            return cursor.rowcount > 0

    def delete_by_name(self, name: str) -> bool:
        """Delete a snippet by name."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM snippets WHERE name = ?", (name,)
            )
            return cursor.rowcount > 0

    def list_all(self) -> List[Snippet]:
        """List all snippets."""
        self.init_db()
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snippets ORDER BY updated_at DESC"
            )
            rows = cursor.fetchall()
            return [Snippet.from_db_dict(dict(row)) for row in rows]

    def search(
        self,
        query: Optional[str] = None,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Snippet]:
        """Search snippets with optional filters."""
        self.init_db()
        conditions = []
        params = []

        if query:
            conditions.append("(name LIKE ? OR content LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        if language:
            conditions.append("language = ?")
            params.append(language)

        if tags:
            # Search for snippets containing any of the tags
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f'%"{tag}"%')
            if tag_conditions:
                conditions.append(f"({' OR '.join(tag_conditions)})")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with self.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM snippets WHERE {where_clause} ORDER BY updated_at DESC",
                params,
            )
            rows = cursor.fetchall()
            return [Snippet.from_db_dict(dict(row)) for row in rows]

    def get_all_tags(self) -> List[tuple]:
        """Get all unique tags with their counts."""
        self.init_db()
        import json

        with self.get_connection() as conn:
            cursor = conn.execute("SELECT tags FROM snippets WHERE tags != '[]'")
            rows = cursor.fetchall()

            tag_counts = {}
            for row in rows:
                tags = json.loads(row["tags"])
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)


# Global database instance
db = Database()

