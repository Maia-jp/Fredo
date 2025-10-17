"""Snippet execution engine for Fredo."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

from fredo.core.models import Snippet


class SnippetRunner:
    """Executes code snippets."""

    # Map of language names to executor configurations
    EXECUTORS = {
        "python": {"cmd": ["python3"], "use_file": True},
        "python3": {"cmd": ["python3"], "use_file": True},
        "bash": {"cmd": ["bash"], "use_file": True},
        "sh": {"cmd": ["sh"], "use_file": True},
        "shell": {"cmd": ["bash"], "use_file": True},
        "javascript": {"cmd": ["node"], "use_file": True},
        "js": {"cmd": ["node"], "use_file": True},
        "typescript": {"cmd": ["ts-node"], "use_file": True},
        "ts": {"cmd": ["ts-node"], "use_file": True},
        "ruby": {"cmd": ["ruby"], "use_file": True},
        "rb": {"cmd": ["ruby"], "use_file": True},
        "go": {"cmd": ["go", "run"], "use_file": True},
        "rust": {"cmd": ["rust-script"], "use_file": True},
        "php": {"cmd": ["php"], "use_file": True},
        "perl": {"cmd": ["perl"], "use_file": True},
        "lua": {"cmd": ["lua"], "use_file": True},
        "r": {"cmd": ["Rscript"], "use_file": True},
    }

    def detect_language(self, snippet: Snippet) -> str:
        """Detect the language of a snippet."""
        # 1. Check if language is explicitly set (and not 'auto')
        if snippet.language and snippet.language.lower() != "auto":
            return snippet.language.lower()

        # 2. Check for shebang
        lines = snippet.content.strip().split("\n")
        if lines and lines[0].startswith("#!"):
            shebang = lines[0][2:].strip()
            if "python" in shebang:
                return "python"
            elif "bash" in shebang or "sh" in shebang:
                return "bash"
            elif "node" in shebang:
                return "javascript"
            elif "ruby" in shebang:
                return "ruby"

        # 3. Use Pygments to guess the language
        try:
            lexer = guess_lexer(snippet.content)
            lang_name = lexer.name.lower()
            # Map Pygments names to our executor names
            if "python" in lang_name:
                return "python"
            elif "bash" in lang_name or "shell" in lang_name:
                return "bash"
            elif "javascript" in lang_name:
                return "javascript"
            elif "ruby" in lang_name:
                return "ruby"
            return lang_name
        except ClassNotFound:
            pass

        # Default to bash if we can't determine
        return "bash"

    def can_execute(self, language: str) -> Tuple[bool, Optional[str]]:
        """Check if we can execute the given language."""
        language = language.lower()

        if language not in self.EXECUTORS:
            return False, f"Unsupported language: {language}"

        executor = self.EXECUTORS[language]
        cmd = executor["cmd"][0]

        # Check if the command is available
        if not shutil.which(cmd):
            return False, f"Command '{cmd}' not found. Please install it first."

        return True, None

    def run(
        self,
        snippet: Snippet,
        cwd: Optional[str] = None,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """Execute a snippet.

        Args:
            snippet: The snippet to execute
            cwd: Working directory (if None, uses snippet's execution_mode)
            capture_output: Whether to capture output

        Returns:
            CompletedProcess object with execution results
        """
        language = self.detect_language(snippet)
        can_exec, error = self.can_execute(language)

        if not can_exec:
            raise RuntimeError(error)

        executor = self.EXECUTORS[language]

        # Determine working directory
        if cwd is None:
            if snippet.execution_mode == "isolated":
                cwd = tempfile.mkdtemp(prefix="fredo_")
            else:
                cwd = os.getcwd()

        # Create temporary file for the snippet
        temp_file = None
        try:
            # Always use file for execution
            suffix = snippet.get_file_extension()
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=suffix,
                delete=False,
                dir=cwd,
            ) as f:
                f.write(snippet.content)
                temp_file = f.name

            # Make the file executable if it's a shell script
            if language in ["bash", "sh", "shell"]:
                os.chmod(temp_file, 0o755)

            # Build command
            cmd = executor["cmd"] + [temp_file]

            # Execute
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
            )

            return result

        finally:
            # Cleanup temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

            # Cleanup temporary directory if in isolated mode
            if snippet.execution_mode == "isolated" and cwd != os.getcwd():
                try:
                    shutil.rmtree(cwd, ignore_errors=True)
                except Exception:
                    pass


# Global runner instance
runner = SnippetRunner()

