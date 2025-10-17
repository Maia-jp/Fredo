"""Editor integration for Fredo."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from fredo.utils.config import config_manager


class EditorError(Exception):
    """Exception raised when editor operations fail."""

    pass


class EditorManager:
    """Manages editor integration."""

    def get_editor(self) -> str:
        """Get the editor command to use."""
        return config_manager.get_editor()

    def edit_content(
        self,
        content: str = "",
        extension: str = ".txt",
        message: Optional[str] = None,
    ) -> Optional[str]:
        """Open editor to edit content.

        Args:
            content: Initial content to edit
            extension: File extension for syntax highlighting
            message: Optional message to show at the top of the file

        Returns:
            Edited content, or None if user canceled

        Raises:
            EditorError: If editor execution fails
        """
        editor = self.get_editor()

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=extension,
            delete=False,
        ) as f:
            temp_file = Path(f.name)

            # Write message as comment if provided
            if message:
                comment_char = self._get_comment_char(extension)
                f.write(f"{comment_char} {message}\n")
                f.write(f"{comment_char} Delete these lines when done.\n\n")

            # Write initial content
            f.write(content)

        try:
            # Open editor
            result = subprocess.run(
                [editor, str(temp_file)],
                check=False,
            )

            # Check if user canceled (some editors return non-zero on cancel)
            if result.returncode != 0:
                # Read the file anyway - some editors exit with non-zero even on success
                pass

            # Read edited content
            edited_content = temp_file.read_text()

            # Remove message lines if present
            if message:
                lines = edited_content.split("\n")
                # Remove comment lines at the start
                comment_char = self._get_comment_char(extension)
                while lines and lines[0].strip().startswith(comment_char):
                    lines.pop(0)
                # Remove empty lines at the start
                while lines and not lines[0].strip():
                    lines.pop(0)
                edited_content = "\n".join(lines)

            # Check if content is empty or only whitespace
            if not edited_content or not edited_content.strip():
                return None

            return edited_content.strip() + "\n"  # Ensure single trailing newline

        except Exception as e:
            raise EditorError(f"Failed to open editor: {e}")

        finally:
            # Cleanup temporary file
            try:
                temp_file.unlink()
            except Exception:
                pass

    def _get_comment_char(self, extension: str) -> str:
        """Get appropriate comment character for file extension."""
        comment_map = {
            ".py": "#",
            ".sh": "#",
            ".bash": "#",
            ".rb": "#",
            ".r": "#",
            ".yaml": "#",
            ".yml": "#",
            ".toml": "#",
            ".js": "//",
            ".ts": "//",
            ".java": "//",
            ".c": "//",
            ".cpp": "//",
            ".cs": "//",
            ".go": "//",
            ".rs": "//",
            ".php": "//",
            ".sql": "--",
            ".lua": "--",
            ".html": "<!--",
            ".css": "/*",
        }
        return comment_map.get(extension.lower(), "#")


# Global editor manager instance
editor_manager = EditorManager()

