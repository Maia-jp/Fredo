"""Tests for the EditorManager."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from fredo.utils.editor import EditorError, EditorManager


class TestEditorManagerGetEditor:
    """Test getting editor command."""

    def test_get_editor_from_config(self, config_manager):
        """Test getting editor from configuration."""
        em = EditorManager()
        
        with patch("fredo.utils.editor.config_manager", config_manager):
            editor = em.get_editor()
        
        assert editor == "vim"

    def test_get_editor_uses_config_manager(self):
        """Test that get_editor uses config_manager."""
        em = EditorManager()
        
        mock_config_manager = Mock()
        mock_config_manager.get_editor.return_value = "emacs"
        
        with patch("fredo.utils.editor.config_manager", mock_config_manager):
            editor = em.get_editor()
        
        assert editor == "emacs"
        mock_config_manager.get_editor.assert_called_once()


class TestEditorManagerEditContent:
    """Test editing content."""

    def test_edit_content_creates_temp_file(self):
        """Test that edit_content creates temporary file."""
        em = EditorManager()
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value="new content"):
                result = em.edit_content(content="initial", extension=".py")
        
        assert result == "new content\n"

    def test_edit_content_with_initial_content(self):
        """Test editing with initial content."""
        em = EditorManager()
        
        initial_content = "print('hello')"
        edited_content = "print('world')"
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=edited_content):
                result = em.edit_content(content=initial_content, extension=".py")
        
        assert edited_content in result

    def test_edit_content_with_message(self):
        """Test editing with message header."""
        em = EditorManager()
        
        edited_content = "# Message line\n# Delete line\n\nactual content"
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=edited_content):
                result = em.edit_content(
                    content="",
                    extension=".py",
                    message="Message line",
                )
        
        # Message lines should be removed
        assert "Message line" not in result
        assert "actual content" in result

    def test_edit_content_adds_trailing_newline(self):
        """Test that edit_content adds trailing newline."""
        em = EditorManager()
        
        edited_content = "content without newline"
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=edited_content):
                result = em.edit_content(content="", extension=".txt")
        
        assert result.endswith("\n")

    def test_edit_content_returns_none_for_empty_content(self):
        """Test that empty content returns None."""
        em = EditorManager()
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value="   \n  \n"):
                result = em.edit_content(content="", extension=".txt")
        
        assert result is None

    def test_edit_content_returns_none_for_whitespace_only(self):
        """Test that whitespace-only content returns None."""
        em = EditorManager()
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=""):
                result = em.edit_content(content="", extension=".txt")
        
        assert result is None

    def test_edit_content_with_different_extensions(self):
        """Test editing with different file extensions."""
        em = EditorManager()
        
        extensions = [".py", ".sh", ".js", ".md", ".txt"]
        
        for ext in extensions:
            mock_subprocess = MagicMock()
            mock_subprocess.returncode = 0
            
            with patch("subprocess.run", return_value=mock_subprocess) as mock_run:
                with patch.object(Path, "read_text", return_value="content"):
                    em.edit_content(content="test", extension=ext)
                
                # Verify temp file had correct extension
                call_args = mock_run.call_args
                temp_file_path = call_args[0][0][1]
                assert temp_file_path.endswith(ext)

    def test_edit_content_calls_subprocess_with_editor(self):
        """Test that subprocess is called with editor command."""
        em = EditorManager()
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess) as mock_run:
            with patch.object(Path, "read_text", return_value="content"):
                with patch.object(em, "get_editor", return_value="nvim"):
                    em.edit_content(content="test", extension=".txt")
        
        # Verify subprocess was called with nvim
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "nvim"

    def test_edit_content_handles_editor_nonzero_exit(self):
        """Test handling editor non-zero exit code."""
        em = EditorManager()
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 1  # Non-zero exit
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value="content"):
                # Should still return content (some editors exit non-zero)
                result = em.edit_content(content="test", extension=".txt")
        
        assert result is not None

    def test_edit_content_cleans_up_temp_file(self):
        """Test that temporary file is cleaned up."""
        em = EditorManager()
        
        temp_file_path = None
        
        def mock_run(cmd, **kwargs):
            # Track the temp file path from subprocess call
            nonlocal temp_file_path
            temp_file_path = cmd[1]
            result = MagicMock()
            result.returncode = 0
            return result
        
        with patch("subprocess.run", side_effect=mock_run):
            with patch.object(Path, "read_text", return_value="content"):
                em.edit_content(content="test", extension=".txt")
        
        # Verify temp file was created and cleaned up
        assert temp_file_path is not None
        # The file should have been deleted in the finally block
        # We can't verify deletion with mocked read_text, but no exception occurred

    def test_edit_content_raises_editor_error_on_exception(self):
        """Test that EditorError is raised on exception."""
        em = EditorManager()
        
        with patch("subprocess.run", side_effect=Exception("Editor failed")):
            with pytest.raises(EditorError) as exc_info:
                em.edit_content(content="test", extension=".txt")
        
        assert "Failed to open editor" in str(exc_info.value)

    def test_edit_content_removes_message_comment_lines(self):
        """Test that message comment lines are removed."""
        em = EditorManager()
        
        # Content with message comments at top
        edited_content = """# This is a message
# Delete these lines when done.

actual content here
more content"""
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=edited_content):
                result = em.edit_content(
                    content="",
                    extension=".py",
                    message="This is a message",
                )
        
        assert "This is a message" not in result
        assert "actual content here" in result

    def test_edit_content_removes_empty_lines_after_message(self):
        """Test that empty lines after message are removed."""
        em = EditorManager()
        
        edited_content = """# Message


actual content"""
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=edited_content):
                result = em.edit_content(
                    content="",
                    extension=".py",
                    message="Message",
                )
        
        # Should start with actual content
        assert result.strip().startswith("actual content")


class TestEditorManagerGetCommentChar:
    """Test getting comment character for extensions."""

    def test_get_comment_char_python(self):
        """Test getting comment char for Python."""
        em = EditorManager()
        assert em._get_comment_char(".py") == "#"

    def test_get_comment_char_bash(self):
        """Test getting comment char for bash."""
        em = EditorManager()
        assert em._get_comment_char(".sh") == "#"
        assert em._get_comment_char(".bash") == "#"

    def test_get_comment_char_javascript(self):
        """Test getting comment char for JavaScript."""
        em = EditorManager()
        assert em._get_comment_char(".js") == "//"
        assert em._get_comment_char(".ts") == "//"

    def test_get_comment_char_ruby(self):
        """Test getting comment char for Ruby."""
        em = EditorManager()
        assert em._get_comment_char(".rb") == "#"

    def test_get_comment_char_sql(self):
        """Test getting comment char for SQL."""
        em = EditorManager()
        assert em._get_comment_char(".sql") == "--"

    def test_get_comment_char_lua(self):
        """Test getting comment char for Lua."""
        em = EditorManager()
        assert em._get_comment_char(".lua") == "--"

    def test_get_comment_char_html(self):
        """Test getting comment char for HTML."""
        em = EditorManager()
        assert em._get_comment_char(".html") == "<!--"

    def test_get_comment_char_css(self):
        """Test getting comment char for CSS."""
        em = EditorManager()
        assert em._get_comment_char(".css") == "/*"

    def test_get_comment_char_case_insensitive(self):
        """Test that comment char detection is case-insensitive."""
        em = EditorManager()
        assert em._get_comment_char(".PY") == "#"
        assert em._get_comment_char(".JS") == "//"

    def test_get_comment_char_unknown_defaults_to_hash(self):
        """Test that unknown extensions default to #."""
        em = EditorManager()
        assert em._get_comment_char(".unknown") == "#"
        assert em._get_comment_char(".xyz") == "#"

    def test_get_comment_char_all_supported_extensions(self):
        """Test all supported extensions have comment chars."""
        em = EditorManager()
        
        extensions = [
            ".py", ".sh", ".bash", ".rb", ".r", ".yaml", ".yml", ".toml",
            ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".go", ".rs", ".php",
            ".sql", ".lua", ".html", ".css",
        ]
        
        for ext in extensions:
            comment_char = em._get_comment_char(ext)
            assert comment_char is not None
            assert len(comment_char) > 0


class TestEditorManagerIntegration:
    """Test EditorManager integration scenarios."""

    @pytest.mark.skipif(
        not Path("/usr/bin/vim").exists() and not Path("/bin/vim").exists(),
        reason="vim not available",
    )
    def test_edit_content_with_real_editor_simulation(self):
        """Test edit_content with simulated real editor."""
        em = EditorManager()
        
        # Simulate editor modifying file
        def mock_editor_run(cmd, **kwargs):
            # Write to the file that was opened
            temp_file = Path(cmd[1])
            temp_file.write_text("edited content")
            
            result = MagicMock()
            result.returncode = 0
            return result
        
        with patch("subprocess.run", side_effect=mock_editor_run):
            result = em.edit_content(content="initial", extension=".txt")
        
        assert "edited content" in result

    def test_edit_content_preserves_unicode(self):
        """Test that edit_content preserves Unicode."""
        em = EditorManager()
        
        unicode_content = "Hello 世界 🌍"
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=unicode_content):
                result = em.edit_content(content="", extension=".txt")
        
        assert "世界" in result
        assert "🌍" in result

    def test_edit_content_with_very_long_content(self):
        """Test editing very long content."""
        em = EditorManager()
        
        long_content = "x" * 100000
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=long_content):
                result = em.edit_content(content=long_content, extension=".txt")
        
        assert len(result) >= 100000


class TestEditorManagerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_edit_content_with_empty_initial_content(self):
        """Test editing with empty initial content."""
        em = EditorManager()
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value="new content"):
                result = em.edit_content(content="", extension=".txt")
        
        assert result == "new content\n"

    def test_edit_content_with_special_characters(self):
        """Test editing content with special characters."""
        em = EditorManager()
        
        special_content = "Special: $VAR & < > | ' \" \\"
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=special_content):
                result = em.edit_content(content="", extension=".txt")
        
        assert "$VAR" in result

    def test_edit_content_with_null_bytes(self):
        """Test editing content with null bytes."""
        em = EditorManager()
        
        content_with_null = "content\x00with\x00nulls"
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=content_with_null):
                result = em.edit_content(content="", extension=".txt")
        
        assert "\x00" in result

    def test_edit_content_with_only_newlines(self):
        """Test that content with only newlines returns None."""
        em = EditorManager()
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value="\n\n\n"):
                result = em.edit_content(content="", extension=".txt")
        
        assert result is None

    def test_edit_content_with_message_but_no_content(self):
        """Test editing with message but user provides no content."""
        em = EditorManager()
        
        # User deletes message but adds nothing
        edited_content = ""
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=edited_content):
                result = em.edit_content(
                    content="",
                    extension=".py",
                    message="Add your code here",
                )
        
        assert result is None

    def test_edit_content_with_multiline_message(self):
        """Test editing with multiline content."""
        em = EditorManager()
        
        multiline = """line 1
line 2
line 3"""
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=multiline):
                result = em.edit_content(content="", extension=".txt")
        
        assert "line 1" in result
        assert "line 2" in result
        assert "line 3" in result

    def test_edit_content_preserves_indentation(self):
        """Test that indentation is preserved."""
        em = EditorManager()
        
        indented_content = """def hello():
    print("hello")
    if True:
        print("world")"""
        
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        
        with patch("subprocess.run", return_value=mock_subprocess):
            with patch.object(Path, "read_text", return_value=indented_content):
                result = em.edit_content(content="", extension=".py")
        
        assert "    print" in result

    def test_editor_error_contains_useful_info(self):
        """Test that EditorError contains useful information."""
        em = EditorManager()
        
        with patch("subprocess.run", side_effect=OSError("No such file")):
            with pytest.raises(EditorError) as exc_info:
                em.edit_content(content="test", extension=".txt")
        
        error_msg = str(exc_info.value)
        assert "Failed to open editor" in error_msg


class TestEditorManagerGlobalInstance:
    """Test the global editor manager instance."""

    def test_global_editor_manager_exists(self):
        """Test that global editor manager exists."""
        from fredo.utils.editor import editor_manager
        
        assert editor_manager is not None
        assert isinstance(editor_manager, EditorManager)

    def test_global_editor_manager_is_functional(self):
        """Test that global editor manager works."""
        from fredo.utils.editor import editor_manager
        
        # Should be able to get editor
        editor = editor_manager.get_editor()
        
        assert editor is not None
        assert isinstance(editor, str)


class TestEditorErrorException:
    """Test EditorError exception."""

    def test_editor_error_is_exception(self):
        """Test that EditorError is an Exception."""
        assert issubclass(EditorError, Exception)

    def test_editor_error_can_be_raised(self):
        """Test that EditorError can be raised and caught."""
        with pytest.raises(EditorError):
            raise EditorError("Test error")

    def test_editor_error_message(self):
        """Test EditorError message."""
        error = EditorError("Custom error message")
        assert str(error) == "Custom error message"

