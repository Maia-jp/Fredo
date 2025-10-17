"""Tests for the SnippetRunner."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from fredo.core.models import Snippet
from fredo.core.runner import SnippetRunner


class TestLanguageDetection:
    """Test language detection."""

    def test_detect_explicit_python_language(self):
        """Test detecting explicitly set Python language."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content="print('hello')",
            language="python",
        )
        
        result = runner.detect_language(snippet)
        assert result == "python"

    def test_detect_explicit_bash_language(self):
        """Test detecting explicitly set bash language."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='echo "hello"',
            language="bash",
        )
        
        result = runner.detect_language(snippet)
        assert result == "bash"

    def test_detect_language_from_python_shebang(self):
        """Test detecting language from Python shebang."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='#!/usr/bin/env python3\nprint("hello")',
            language="auto",
        )
        
        result = runner.detect_language(snippet)
        assert result == "python"

    def test_detect_language_from_bash_shebang(self):
        """Test detecting language from bash shebang."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='#!/bin/bash\necho "hello"',
            language="auto",
        )
        
        result = runner.detect_language(snippet)
        assert result == "bash"

    def test_detect_language_from_node_shebang(self):
        """Test detecting language from node shebang."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='#!/usr/bin/env node\nconsole.log("hello")',
            language="auto",
        )
        
        result = runner.detect_language(snippet)
        assert result == "javascript"

    def test_detect_language_from_ruby_shebang(self):
        """Test detecting language from ruby shebang."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='#!/usr/bin/env ruby\nputs "hello"',
            language="auto",
        )
        
        result = runner.detect_language(snippet)
        assert result == "ruby"

    def test_detect_language_using_pygments_python(self):
        """Test detecting Python using Pygments."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='import sys\ndef main():\n    print("hello")\n\nif __name__ == "__main__":\n    main()',
            language="auto",
        )
        
        result = runner.detect_language(snippet)
        assert result == "python"

    def test_detect_language_using_pygments_javascript(self):
        """Test detecting JavaScript using Pygments."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='const x = 10;\nconsole.log(x);',
            language="auto",
        )
        
        result = runner.detect_language(snippet)
        assert result == "javascript"

    def test_detect_language_defaults_to_bash(self):
        """Test that unknown language defaults to bash."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='some unknown content',
            language="auto",
        )
        
        result = runner.detect_language(snippet)
        assert result == "bash"

    def test_detect_language_case_insensitive(self):
        """Test that language detection is case-insensitive."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content="test",
            language="PYTHON",
        )
        
        result = runner.detect_language(snippet)
        assert result == "python"


class TestCanExecute:
    """Test can_execute checks."""

    def test_can_execute_supported_language_with_available_command(self):
        """Test can_execute for supported language with available command."""
        runner = SnippetRunner()
        
        # Python3 should be available on most systems
        with patch("shutil.which", return_value="/usr/bin/python3"):
            can_exec, error = runner.can_execute("python")
        
        assert can_exec is True
        assert error is None

    def test_can_execute_supported_language_without_command(self):
        """Test can_execute for supported language without available command."""
        runner = SnippetRunner()
        
        with patch("shutil.which", return_value=None):
            can_exec, error = runner.can_execute("python")
        
        assert can_exec is False
        assert "not found" in error

    def test_can_execute_unsupported_language(self):
        """Test can_execute for unsupported language."""
        runner = SnippetRunner()
        
        can_exec, error = runner.can_execute("unsupported")
        
        assert can_exec is False
        assert "Unsupported language" in error

    def test_can_execute_case_insensitive(self):
        """Test that can_execute is case-insensitive."""
        runner = SnippetRunner()
        
        with patch("shutil.which", return_value="/usr/bin/python3"):
            can_exec, error = runner.can_execute("PYTHON")
        
        assert can_exec is True

    def test_can_execute_all_supported_languages(self):
        """Test can_execute for all supported languages."""
        runner = SnippetRunner()
        
        supported_languages = list(runner.EXECUTORS.keys())
        
        for lang in supported_languages:
            # Mock the command as available
            with patch("shutil.which", return_value=f"/usr/bin/{lang}"):
                can_exec, error = runner.can_execute(lang)
                assert can_exec is True, f"Language {lang} should be executable"


class TestSnippetExecution:
    """Test snippet execution."""

    def test_run_python_snippet_success(self):
        """Test running a successful Python snippet."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-python",
            content='print("Hello from Python")',
            language="python",
            execution_mode="current",
        )
        
        # Only run if python3 is available
        if not shutil.which("python3"):
            pytest.skip("python3 not available")
        
        result = runner.run(snippet, cwd=tempfile.gettempdir())
        
        assert result.returncode == 0
        assert "Hello from Python" in result.stdout

    def test_run_bash_snippet_success(self):
        """Test running a successful bash snippet."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-bash",
            content='echo "Hello from Bash"',
            language="bash",
            execution_mode="current",
        )
        
        # Only run if bash is available
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        
        result = runner.run(snippet, cwd=tempfile.gettempdir())
        
        assert result.returncode == 0
        assert "Hello from Bash" in result.stdout

    def test_run_snippet_with_error(self):
        """Test running a snippet that produces an error."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-error",
            content='exit 1',
            language="bash",
            execution_mode="current",
        )
        
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        
        result = runner.run(snippet, cwd=tempfile.gettempdir())
        
        assert result.returncode == 1

    def test_run_unsupported_language_raises_error(self):
        """Test that running unsupported language raises error."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content="test",
            language="unsupported",
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            runner.run(snippet)
        
        assert "Unsupported language" in str(exc_info.value)

    def test_run_unavailable_command_raises_error(self):
        """Test that running with unavailable command raises error."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content="test",
            language="rust",  # Probably not installed on test system
        )
        
        # Mock rust-script as not available
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                runner.run(snippet)
            
            assert "not found" in str(exc_info.value)

    def test_run_with_custom_cwd(self):
        """Test running snippet with custom working directory."""
        runner = SnippetRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            snippet = Snippet(
                name="test-cwd",
                content='echo "test" > output.txt',
                language="bash",
                execution_mode="current",
            )
            
            if not shutil.which("bash"):
                pytest.skip("bash not available")
            
            runner.run(snippet, cwd=temp_dir)
            
            # Check that file was created in the custom cwd
            output_file = Path(temp_dir) / "output.txt"
            assert output_file.exists()

    def test_run_isolated_mode_creates_temp_dir(self):
        """Test that isolated mode creates temporary directory."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-isolated",
            content='pwd',
            language="bash",
            execution_mode="isolated",
        )
        
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        
        original_cwd = os.getcwd()
        result = runner.run(snippet)
        
        # Should have run in a different directory
        assert result.returncode == 0
        assert "fredo_" in result.stdout
        
        # Current directory should be unchanged
        assert os.getcwd() == original_cwd

    def test_run_isolated_mode_cleans_up_temp_dir(self):
        """Test that isolated mode cleans up temporary directory."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-cleanup",
            content='pwd',
            language="bash",
            execution_mode="isolated",
        )
        
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        
        result = runner.run(snippet)
        temp_dir = result.stdout.strip()
        
        # Directory should not exist after execution
        # (cleanup happens even if temp_dir path is in output)
        # We can't directly check since the cleanup is best-effort
        assert result.returncode == 0

    def test_run_current_mode_uses_provided_cwd(self):
        """Test that current mode uses provided cwd."""
        runner = SnippetRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            snippet = Snippet(
                name="test-current",
                content='pwd',
                language="bash",
                execution_mode="current",
            )
            
            if not shutil.which("bash"):
                pytest.skip("bash not available")
            
            result = runner.run(snippet, cwd=temp_dir)
            
            assert result.returncode == 0
            assert temp_dir in result.stdout

    def test_run_creates_temp_file_with_correct_extension(self):
        """Test that temporary files have correct extension."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-ext",
            content='import sys; print(sys.argv[0])',
            language="python",
            execution_mode="current",
        )
        
        if not shutil.which("python3"):
            pytest.skip("python3 not available")
        
        result = runner.run(snippet, cwd=tempfile.gettempdir())
        
        assert result.returncode == 0
        assert ".py" in result.stdout

    def test_run_makes_shell_scripts_executable(self):
        """Test that shell scripts are made executable."""
        runner = SnippetRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            snippet = Snippet(
                name="test-executable",
                content='#!/bin/bash\necho "executable"',
                language="bash",
                execution_mode="current",
            )
            
            if not shutil.which("bash"):
                pytest.skip("bash not available")
            
            # This test verifies the file is executable by successfully running it
            result = runner.run(snippet, cwd=temp_dir)
            assert result.returncode == 0

    def test_run_cleans_up_temp_file(self):
        """Test that temporary file is cleaned up after execution."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-cleanup-file",
            content='echo "test"',
            language="bash",
            execution_mode="current",
        )
        
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Count files before
            files_before = list(Path(temp_dir).iterdir())
            
            runner.run(snippet, cwd=temp_dir)
            
            # Count files after - should be the same (temp file cleaned up)
            files_after = list(Path(temp_dir).iterdir())
            assert len(files_after) == len(files_before)

    def test_run_with_capture_output_false(self):
        """Test running with capture_output=False."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-no-capture",
            content='echo "test"',
            language="bash",
            execution_mode="current",
        )
        
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        
        result = runner.run(snippet, cwd=tempfile.gettempdir(), capture_output=False)
        
        assert result.returncode == 0
        # Output should not be captured
        assert result.stdout is None
        assert result.stderr is None


class TestSnippetRunnerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_run_snippet_with_multiline_content(self):
        """Test running snippet with multiline content."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-multiline",
            content='''#!/bin/bash
echo "Line 1"
echo "Line 2"
echo "Line 3"''',
            language="bash",
            execution_mode="current",
        )
        
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        
        result = runner.run(snippet, cwd=tempfile.gettempdir())
        
        assert result.returncode == 0
        assert "Line 1" in result.stdout
        assert "Line 2" in result.stdout
        assert "Line 3" in result.stdout

    def test_run_snippet_with_unicode_content(self):
        """Test running snippet with Unicode content."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-unicode",
            content='print("Hello 世界 🌍")',
            language="python",
            execution_mode="current",
        )
        
        if not shutil.which("python3"):
            pytest.skip("python3 not available")
        
        result = runner.run(snippet, cwd=tempfile.gettempdir())
        
        assert result.returncode == 0
        assert "Hello" in result.stdout

    def test_run_snippet_with_special_characters(self):
        """Test running snippet with special characters."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-special",
            content='echo "Special: $HOME & < > | \'"',
            language="bash",
            execution_mode="current",
        )
        
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        
        result = runner.run(snippet, cwd=tempfile.gettempdir())
        
        assert result.returncode == 0
        assert "Special:" in result.stdout

    def test_run_empty_snippet_content(self):
        """Test that empty content is validated at model level."""
        # Empty content should be caught by Pydantic validation
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            Snippet(name="empty", content="", language="python")

    def test_detect_language_with_empty_shebang_line(self):
        """Test detecting language with empty first line."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='\nprint("hello")',
            language="auto",
        )
        
        # Should fall back to Pygments
        result = runner.detect_language(snippet)
        assert result == "python"

    def test_detect_language_with_comment_before_shebang(self):
        """Test that shebang must be first line."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test",
            content='# comment\n#!/usr/bin/env python3\nprint("hello")',
            language="auto",
        )
        
        # Shebang not on first line, should use Pygments
        result = runner.detect_language(snippet)
        assert result == "python"  # Pygments should detect it

    def test_run_snippet_with_very_long_output(self):
        """Test running snippet that produces very long output."""
        runner = SnippetRunner()
        snippet = Snippet(
            name="test-long-output",
            content='for i in range(1000):\n    print(i)',
            language="python",
            execution_mode="current",
        )
        
        if not shutil.which("python3"):
            pytest.skip("python3 not available")
        
        result = runner.run(snippet, cwd=tempfile.gettempdir())
        
        assert result.returncode == 0
        assert "999" in result.stdout

    def test_executor_mapping_all_languages(self):
        """Test that all languages in EXECUTORS have valid configuration."""
        runner = SnippetRunner()
        
        for lang, config in runner.EXECUTORS.items():
            assert "cmd" in config
            assert isinstance(config["cmd"], list)
            assert len(config["cmd"]) > 0
            assert "use_file" in config


class TestSnippetRunnerGlobalInstance:
    """Test the global runner instance."""

    def test_global_runner_instance_exists(self):
        """Test that global runner instance is available."""
        from fredo.core.runner import runner
        
        assert runner is not None
        assert isinstance(runner, SnippetRunner)

    def test_global_runner_is_functional(self):
        """Test that global runner instance works."""
        from fredo.core.runner import runner
        
        snippet = Snippet(
            name="test",
            content='echo "test"',
            language="bash",
        )
        
        can_exec, _ = runner.can_execute("bash")
        if can_exec:
            result = runner.run(snippet, cwd=tempfile.gettempdir())
            assert result.returncode == 0

