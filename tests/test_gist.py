"""Tests for the GistManager."""

from unittest.mock import Mock, PropertyMock, patch

import pytest
from github import GithubException

from fredo.core.models import Snippet
from fredo.integrations.gist import GistError, GistManager


class TestGistManagerInitialization:
    """Test GistManager initialization."""

    def test_gist_manager_initializes(self):
        """Test that GistManager initializes correctly."""
        gm = GistManager()
        
        assert gm._github is None  # Not initialized yet

    def test_get_github_creates_client(self, config_manager):
        """Test that _get_github creates GitHub client."""
        gm = GistManager()
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch("fredo.integrations.gist.Github") as mock_github:
                gh = gm._get_github()
                
                mock_github.assert_called_once_with("test_token_123")

    def test_get_github_raises_error_without_token(self, temp_dir, monkeypatch):
        """Test that _get_github raises error without token."""
        from fredo.utils.config import ConfigManager, FredoConfig
        
        cm = ConfigManager()
        cm.config_dir = temp_dir
        cm.config_file = temp_dir / "config.toml"
        cm._config = FredoConfig(github_token=None)
        
        gm = GistManager()
        
        with patch("fredo.integrations.gist.config_manager", cm):
            with pytest.raises(GistError) as exc_info:
                gm._get_github()
        
        assert "token not configured" in str(exc_info.value).lower()

    def test_get_github_caches_client(self, config_manager):
        """Test that _get_github caches GitHub client."""
        gm = GistManager()
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch("fredo.integrations.gist.Github") as mock_github:
                gh1 = gm._get_github()
                gh2 = gm._get_github()
                
                # Should only create once
                assert mock_github.call_count == 1
                assert gh1 is gh2


class TestGistManagerTestConnection:
    """Test connection testing."""

    def test_test_connection_success(self, config_manager, mock_github):
        """Test successful connection test."""
        gm = GistManager()
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_github):
                result = gm.test_connection()
        
        assert result is True

    def test_test_connection_invalid_token(self, config_manager):
        """Test connection with invalid token."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_user = PropertyMock(side_effect=GithubException(401, "Unauthorized"))
        type(mock_gh.get_user()).login = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                mock_gh.get_user.side_effect = GithubException(401, "Unauthorized", None)
                
                with pytest.raises(GistError) as exc_info:
                    gm.test_connection()
        
        assert "Invalid GitHub token" in str(exc_info.value)

    def test_test_connection_network_error(self, config_manager):
        """Test connection with network error."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_user.side_effect = Exception("Network error")
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.test_connection()
        
        assert "Failed to connect" in str(exc_info.value)

    def test_test_connection_other_github_error(self, config_manager):
        """Test connection with other GitHub API error."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_user.side_effect = GithubException(500, "Server error", None)
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.test_connection()
        
        assert "GitHub API error" in str(exc_info.value)


class TestGistManagerCreateGist:
    """Test creating Gists."""

    def test_create_gist_success(self, config_manager, sample_snippet):
        """Test creating a Gist successfully."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_gist.id = "test_gist_id"
        mock_gist.html_url = "https://gist.github.com/user/test_gist_id"
        
        mock_user = Mock()
        mock_user.create_gist.return_value = mock_gist
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                result = gm.create_gist(sample_snippet, private=True)
        
        assert result == mock_gist
        mock_user.create_gist.assert_called_once()

    def test_create_gist_private_by_default(
        self, config_manager, sample_snippet
    ):
        """Test that Gists are private by default."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_user = Mock()
        mock_user.create_gist.return_value = mock_gist
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                gm.create_gist(sample_snippet, private=True)
        
        # Check that public=False was passed
        call_kwargs = mock_user.create_gist.call_args[1]
        assert call_kwargs["public"] is False

    def test_create_gist_public(self, config_manager, sample_snippet):
        """Test creating a public Gist."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_user = Mock()
        mock_user.create_gist.return_value = mock_gist
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                gm.create_gist(sample_snippet, private=False)
        
        call_kwargs = mock_user.create_gist.call_args[1]
        assert call_kwargs["public"] is True

    def test_create_gist_includes_tags_in_description(
        self, config_manager, sample_snippet
    ):
        """Test that Gist description includes tags."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_user = Mock()
        mock_user.create_gist.return_value = mock_gist
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                gm.create_gist(sample_snippet)
        
        call_kwargs = mock_user.create_gist.call_args[1]
        description = call_kwargs["description"]
        
        assert "test" in description
        assert "hello-world" in description

    def test_create_gist_with_correct_filename(
        self, config_manager, sample_snippet
    ):
        """Test that Gist uses correct filename with extension."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_user = Mock()
        mock_user.create_gist.return_value = mock_gist
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_gh
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                gm.create_gist(sample_snippet)
        
        call_kwargs = mock_user.create_gist.call_args[1]
        files = call_kwargs["files"]
        
        # Should have filename with .py extension
        assert "test-snippet.py" in files

    def test_create_gist_handles_github_exception(
        self, config_manager, sample_snippet
    ):
        """Test handling GitHub exception when creating Gist."""
        gm = GistManager()
        
        mock_user = Mock()
        mock_user.create_gist.side_effect = GithubException(
            403, "Rate limit exceeded", None
        )
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.create_gist(sample_snippet)
        
        assert "Failed to create Gist" in str(exc_info.value)

    def test_create_gist_handles_generic_exception(
        self, config_manager, sample_snippet
    ):
        """Test handling generic exception when creating Gist."""
        gm = GistManager()
        
        mock_user = Mock()
        mock_user.create_gist.side_effect = Exception("Unexpected error")
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.create_gist(sample_snippet)
        
        assert "Unexpected error creating Gist" in str(exc_info.value)


class TestGistManagerUpdateGist:
    """Test updating Gists."""

    def test_update_gist_success(self, config_manager, sample_snippet):
        """Test updating a Gist successfully."""
        gm = GistManager()
        
        mock_file = Mock()
        mock_file.filename = "old_name.py"
        
        mock_gist = Mock()
        mock_gist.files = {"old_name.py": mock_file}
        mock_gist.edit = Mock()
        
        mock_gh = Mock()
        mock_gh.get_gist.return_value = mock_gist
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                result = gm.update_gist("gist123", sample_snippet)
        
        assert result == mock_gist
        mock_gist.edit.assert_called_once()

    def test_update_gist_updates_content(self, config_manager, sample_snippet):
        """Test that update updates Gist content."""
        gm = GistManager()
        
        mock_file = Mock()
        mock_gist = Mock()
        mock_gist.files = {"test-snippet.py": mock_file}
        
        mock_gh = Mock()
        mock_gh.get_gist.return_value = mock_gist
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                gm.update_gist("gist123", sample_snippet)
        
        call_kwargs = mock_gist.edit.call_args[1]
        files = call_kwargs["files"]
        
        # Should have updated content
        assert "test-snippet.py" in files

    def test_update_gist_renames_file_if_needed(
        self, config_manager, sample_snippet
    ):
        """Test that update renames file if name changed."""
        gm = GistManager()
        
        mock_file = Mock()
        mock_gist = Mock()
        mock_gist.files = {"old_name.py": mock_file}
        
        mock_gh = Mock()
        mock_gh.get_gist.return_value = mock_gist
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                gm.update_gist("gist123", sample_snippet)
        
        call_kwargs = mock_gist.edit.call_args[1]
        files = call_kwargs["files"]
        
        # Should have both old (for deletion) and new filename
        assert "old_name.py" in files or "test-snippet.py" in files

    def test_update_gist_handles_not_found(
        self, config_manager, sample_snippet
    ):
        """Test handling Gist not found error."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_gist.side_effect = GithubException(404, "Not found", None)
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.update_gist("nonexistent", sample_snippet)
        
        assert "not found" in str(exc_info.value).lower()

    def test_update_gist_handles_generic_exception(
        self, config_manager, sample_snippet
    ):
        """Test handling generic exception when updating."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_gist.side_effect = Exception("Unexpected error")
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.update_gist("gist123", sample_snippet)
        
        assert "Unexpected error updating Gist" in str(exc_info.value)


class TestGistManagerGetGist:
    """Test getting Gists."""

    def test_get_gist_success(self, config_manager, mock_gist):
        """Test getting a Gist successfully."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_gist.return_value = mock_gist
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                result = gm.get_gist("test_gist_id_123")
        
        assert result == mock_gist
        mock_gh.get_gist.assert_called_once_with("test_gist_id_123")

    def test_get_gist_not_found(self, config_manager):
        """Test getting nonexistent Gist."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_gist.side_effect = GithubException(404, "Not found", None)
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.get_gist("nonexistent")
        
        assert "not found" in str(exc_info.value).lower()

    def test_get_gist_handles_generic_exception(self, config_manager):
        """Test handling generic exception when getting Gist."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_gist.side_effect = Exception("Network error")
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.get_gist("gist123")
        
        assert "Unexpected error getting Gist" in str(exc_info.value)


class TestGistManagerGistToSnippet:
    """Test converting Gists to Snippets."""

    def test_gist_to_snippet_success(self, mock_gist):
        """Test converting Gist to Snippet successfully."""
        gm = GistManager()
        
        snippet = gm.gist_to_snippet(mock_gist)
        
        assert snippet.name == "test_snippet"
        assert snippet.content == 'print("Hello from Gist")'
        assert snippet.language == "python"
        assert "test" in snippet.tags
        assert "example" in snippet.tags
        assert snippet.gist_id == "test_gist_id_123"
        assert snippet.gist_url == "https://gist.github.com/testuser/test_gist_id_123"

    def test_gist_to_snippet_removes_extension_from_name(self, mock_gist):
        """Test that file extension is removed from snippet name."""
        gm = GistManager()
        
        snippet = gm.gist_to_snippet(mock_gist)
        
        # Name should not include .py extension
        assert snippet.name == "test_snippet"
        assert ".py" not in snippet.name

    def test_gist_to_snippet_handles_no_tags(self):
        """Test converting Gist without tags."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_gist.id = "gist123"
        mock_gist.html_url = "https://gist.github.com/user/gist123"
        mock_gist.description = "Simple description"
        
        mock_file = Mock()
        mock_file.filename = "test.py"
        mock_file.content = "print('test')"
        mock_file.language = "Python"
        
        mock_gist.files = {"test.py": mock_file}
        
        snippet = gm.gist_to_snippet(mock_gist)
        
        assert snippet.tags == []

    def test_gist_to_snippet_handles_no_tags_marker(self):
        """Test converting Gist with 'no tags' marker."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_gist.id = "gist123"
        mock_gist.html_url = "https://gist.github.com/user/gist123"
        mock_gist.description = "Test (python) - Tags: no tags"
        
        mock_file = Mock()
        mock_file.filename = "test.py"
        mock_file.content = "print('test')"
        mock_file.language = "Python"
        
        mock_gist.files = {"test.py": mock_file}
        
        snippet = gm.gist_to_snippet(mock_gist)
        
        assert snippet.tags == []

    def test_gist_to_snippet_uses_auto_language_if_none(self):
        """Test that 'auto' language is used if Gist has no language."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_gist.id = "gist123"
        mock_gist.html_url = "https://gist.github.com/user/gist123"
        mock_gist.description = "Test"
        
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.content = "content"
        mock_file.language = None
        
        mock_gist.files = {"test.txt": mock_file}
        
        snippet = gm.gist_to_snippet(mock_gist)
        
        assert snippet.language == "auto"

    def test_gist_to_snippet_handles_no_files(self):
        """Test converting Gist with no files raises error."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_gist.files = {}
        
        with pytest.raises(GistError) as exc_info:
            gm.gist_to_snippet(mock_gist)
        
        assert "no files" in str(exc_info.value).lower()

    def test_gist_to_snippet_handles_exception(self):
        """Test handling exception during conversion."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_gist.files = None  # Will cause error
        
        with pytest.raises(GistError) as exc_info:
            gm.gist_to_snippet(mock_gist)
        
        assert "Failed to convert" in str(exc_info.value)


class TestGistManagerListGists:
    """Test listing Gists."""

    def test_list_user_gists_success(self, config_manager):
        """Test listing user's Gists successfully."""
        gm = GistManager()
        
        mock_gist1 = Mock()
        mock_gist2 = Mock()
        mock_gist3 = Mock()
        
        mock_user = Mock()
        mock_user.get_gists.return_value = [mock_gist1, mock_gist2, mock_gist3]
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                result = gm.list_user_gists()
        
        assert len(result) == 3
        assert result[0] == mock_gist1

    def test_list_user_gists_with_limit(self, config_manager):
        """Test listing Gists with limit."""
        gm = GistManager()
        
        mock_gists = [Mock() for _ in range(10)]
        
        mock_user = Mock()
        mock_user.get_gists.return_value = mock_gists
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                result = gm.list_user_gists(limit=5)
        
        assert len(result) == 5

    def test_list_user_gists_empty(self, config_manager):
        """Test listing when user has no Gists."""
        gm = GistManager()
        
        mock_user = Mock()
        mock_user.get_gists.return_value = []
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                result = gm.list_user_gists()
        
        assert result == []

    def test_list_user_gists_handles_github_exception(self, config_manager):
        """Test handling GitHub exception when listing."""
        gm = GistManager()
        
        mock_user = Mock()
        mock_user.get_gists.side_effect = GithubException(
            403, "Rate limit", None
        )
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.list_user_gists()
        
        assert "Failed to list Gists" in str(exc_info.value)

    def test_list_user_gists_handles_generic_exception(self, config_manager):
        """Test handling generic exception when listing."""
        gm = GistManager()
        
        mock_user = Mock()
        mock_user.get_gists.side_effect = Exception("Network error")
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.list_user_gists()
        
        assert "Unexpected error listing Gists" in str(exc_info.value)


class TestGistManagerDeleteGist:
    """Test deleting Gists."""

    def test_delete_gist_success(self, config_manager):
        """Test deleting a Gist successfully."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_gist.delete = Mock()
        
        mock_gh = Mock()
        mock_gh.get_gist.return_value = mock_gist
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                gm.delete_gist("gist123")
        
        mock_gist.delete.assert_called_once()

    def test_delete_gist_not_found(self, config_manager):
        """Test deleting nonexistent Gist."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_gist.side_effect = GithubException(404, "Not found", None)
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.delete_gist("nonexistent")
        
        assert "not found" in str(exc_info.value).lower()

    def test_delete_gist_handles_github_exception(self, config_manager):
        """Test handling GitHub exception when deleting."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_gist.side_effect = GithubException(403, "Forbidden", None)
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.delete_gist("gist123")
        
        assert "Failed to delete Gist" in str(exc_info.value)

    def test_delete_gist_handles_generic_exception(self, config_manager):
        """Test handling generic exception when deleting."""
        gm = GistManager()
        
        mock_gh = Mock()
        mock_gh.get_gist.side_effect = Exception("Network error")
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                with pytest.raises(GistError) as exc_info:
                    gm.delete_gist("gist123")
        
        assert "Unexpected error deleting Gist" in str(exc_info.value)


class TestGistManagerGlobalInstance:
    """Test the global gist manager instance."""

    def test_global_gist_manager_exists(self):
        """Test that global gist manager exists."""
        from fredo.integrations.gist import gist_manager
        
        assert gist_manager is not None
        assert isinstance(gist_manager, GistManager)

    def test_global_gist_manager_not_initialized(self):
        """Test that global gist manager is not initialized by default."""
        from fredo.integrations.gist import gist_manager
        
        # Should not have GitHub client until needed
        assert gist_manager._github is None


class TestGistErrorException:
    """Test GistError exception."""

    def test_gist_error_is_exception(self):
        """Test that GistError is an Exception."""
        assert issubclass(GistError, Exception)

    def test_gist_error_can_be_raised(self):
        """Test that GistError can be raised and caught."""
        with pytest.raises(GistError):
            raise GistError("Test error")

    def test_gist_error_message(self):
        """Test GistError message."""
        error = GistError("Custom error message")
        assert str(error) == "Custom error message"


class TestGistManagerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_gist_with_no_tags(self, config_manager):
        """Test creating Gist for snippet with no tags."""
        gm = GistManager()
        
        snippet = Snippet(name="notags", content="test", tags=[])
        
        mock_gist = Mock()
        mock_user = Mock()
        mock_user.create_gist.return_value = mock_gist
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                gm.create_gist(snippet)
        
        call_kwargs = mock_user.create_gist.call_args[1]
        description = call_kwargs["description"]
        
        assert "no tags" in description

    def test_create_gist_with_unicode_content(self, config_manager):
        """Test creating Gist with Unicode content."""
        gm = GistManager()
        
        snippet = Snippet(
            name="unicode",
            content="print('Hello 世界')",
            language="python",
        )
        
        mock_gist = Mock()
        mock_user = Mock()
        mock_user.create_gist.return_value = mock_gist
        
        mock_gh = Mock()
        mock_gh.get_user.return_value = mock_user
        
        with patch("fredo.integrations.gist.config_manager", config_manager):
            with patch.object(gm, "_get_github", return_value=mock_gh):
                result = gm.create_gist(snippet)
        
        # Should handle Unicode without error
        assert result == mock_gist

    def test_gist_to_snippet_with_name_containing_dots(self):
        """Test converting Gist where filename has multiple dots."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_gist.id = "gist123"
        mock_gist.html_url = "https://gist.github.com/user/gist123"
        mock_gist.description = "Test"
        
        mock_file = Mock()
        mock_file.filename = "test.script.py"
        mock_file.content = "test"
        mock_file.language = "Python"
        
        mock_gist.files = {"test.script.py": mock_file}
        
        snippet = gm.gist_to_snippet(mock_gist)
        
        # Should only remove last extension
        assert snippet.name == "test.script"

    def test_gist_to_snippet_with_no_extension(self):
        """Test converting Gist where filename has no extension."""
        gm = GistManager()
        
        mock_gist = Mock()
        mock_gist.id = "gist123"
        mock_gist.html_url = "https://gist.github.com/user/gist123"
        mock_gist.description = "Test"
        
        mock_file = Mock()
        mock_file.filename = "test_script"
        mock_file.content = "test"
        mock_file.language = "Python"
        
        mock_gist.files = {"test_script": mock_file}
        
        snippet = gm.gist_to_snippet(mock_gist)
        
        assert snippet.name == "test_script"

