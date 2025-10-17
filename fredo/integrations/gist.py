"""GitHub Gist integration for Fredo."""

from typing import List, Optional

from github import Github, GithubException, InputFileContent
from github.Gist import Gist as GithubGist

from fredo.core.models import Snippet
from fredo.utils.config import config_manager


class GistError(Exception):
    """Exception raised when Gist operations fail."""

    pass


class GistManager:
    """Manages GitHub Gist operations."""

    def __init__(self):
        """Initialize Gist manager."""
        self._github = None

    def _get_github(self) -> Github:
        """Get authenticated GitHub client."""
        if self._github is None:
            config = config_manager.load()
            if not config.github_token:
                raise GistError(
                    "GitHub token not configured. Run 'fredo gist setup' first."
                )
            self._github = Github(config.github_token)
        return self._github

    def test_connection(self) -> bool:
        """Test GitHub connection and token validity."""
        try:
            gh = self._get_github()
            gh.get_user().login
            return True
        except GithubException as e:
            if e.status == 401:
                raise GistError("Invalid GitHub token. Please reconfigure.")
            raise GistError(f"GitHub API error: {e}")
        except Exception as e:
            raise GistError(f"Failed to connect to GitHub: {e}")

    def create_gist(
        self,
        snippet: Snippet,
        private: bool = True,
    ) -> GithubGist:
        """Create a new Gist from a snippet.

        Args:
            snippet: The snippet to upload
            private: Whether the Gist should be private

        Returns:
            GitHub Gist object

        Raises:
            GistError: If creation fails
        """
        try:
            gh = self._get_github()
            user = gh.get_user()

            # Create filename with extension
            filename = snippet.name + snippet.get_file_extension()

            # Create description with metadata
            tags_str = ", ".join(snippet.tags) if snippet.tags else "no tags"
            description = (
                f"{snippet.name} ({snippet.language}) - Tags: {tags_str}"
            )

            # Create Gist
            gist = user.create_gist(
                public=not private,
                files={filename: InputFileContent(snippet.content)},
                description=description,
            )

            return gist

        except GithubException as e:
            raise GistError(f"Failed to create Gist: {e}")
        except Exception as e:
            raise GistError(f"Unexpected error creating Gist: {e}")

    def update_gist(
        self,
        gist_id: str,
        snippet: Snippet,
    ) -> GithubGist:
        """Update an existing Gist.

        Args:
            gist_id: The Gist ID to update
            snippet: The snippet with updated content

        Returns:
            GitHub Gist object

        Raises:
            GistError: If update fails
        """
        try:
            gh = self._get_github()
            gist = gh.get_gist(gist_id)

            # Update filename
            filename = snippet.name + snippet.get_file_extension()

            # Update description
            tags_str = ", ".join(snippet.tags) if snippet.tags else "no tags"
            description = (
                f"{snippet.name} ({snippet.language}) - Tags: {tags_str}"
            )

            # Get old filename (first file in gist)
            old_files = list(gist.files.keys())
            old_filename = old_files[0] if old_files else filename

            # Update Gist
            files = {}
            if old_filename != filename:
                # Rename file by deleting old and adding new
                files[old_filename] = InputFileContent("", new_name=filename)

            files[filename] = InputFileContent(snippet.content)

            gist.edit(description=description, files=files)

            return gist

        except GithubException as e:
            if e.status == 404:
                raise GistError(f"Gist {gist_id} not found")
            raise GistError(f"Failed to update Gist: {e}")
        except Exception as e:
            raise GistError(f"Unexpected error updating Gist: {e}")

    def get_gist(self, gist_id: str) -> GithubGist:
        """Get a Gist by ID.

        Args:
            gist_id: The Gist ID

        Returns:
            GitHub Gist object

        Raises:
            GistError: If retrieval fails
        """
        try:
            gh = self._get_github()
            return gh.get_gist(gist_id)
        except GithubException as e:
            if e.status == 404:
                raise GistError(f"Gist {gist_id} not found")
            raise GistError(f"Failed to get Gist: {e}")
        except Exception as e:
            raise GistError(f"Unexpected error getting Gist: {e}")

    def gist_to_snippet(self, gist: GithubGist) -> Snippet:
        """Convert a GitHub Gist to a Snippet.

        Args:
            gist: GitHub Gist object

        Returns:
            Snippet object

        Raises:
            GistError: If conversion fails
        """
        try:
            # Get the first file in the Gist
            files = list(gist.files.values())
            if not files:
                raise GistError("Gist has no files")

            file = files[0]

            # Extract name from filename (remove extension)
            name = file.filename
            if "." in name:
                name = name.rsplit(".", 1)[0]

            # Try to extract tags from description
            tags = []
            if gist.description and "Tags:" in gist.description:
                tags_part = gist.description.split("Tags:")[-1].strip()
                if tags_part and tags_part != "no tags":
                    tags = [t.strip() for t in tags_part.split(",")]

            # Detect language from file
            language = file.language or "auto"

            # Create snippet
            snippet = Snippet(
                name=name,
                content=file.content,
                language=language.lower() if language else "auto",
                tags=tags,
                gist_id=gist.id,
                gist_url=gist.html_url,
            )

            return snippet

        except Exception as e:
            raise GistError(f"Failed to convert Gist to snippet: {e}")

    def list_user_gists(self, limit: Optional[int] = None) -> List[GithubGist]:
        """List user's Gists.

        Args:
            limit: Maximum number of Gists to return

        Returns:
            List of GitHub Gist objects

        Raises:
            GistError: If listing fails
        """
        try:
            gh = self._get_github()
            user = gh.get_user()
            gists = user.get_gists()

            if limit:
                return list(gists[:limit])
            return list(gists)

        except GithubException as e:
            raise GistError(f"Failed to list Gists: {e}")
        except Exception as e:
            raise GistError(f"Unexpected error listing Gists: {e}")

    def delete_gist(self, gist_id: str):
        """Delete a Gist.

        Args:
            gist_id: The Gist ID to delete

        Raises:
            GistError: If deletion fails
        """
        try:
            gh = self._get_github()
            gist = gh.get_gist(gist_id)
            gist.delete()
        except GithubException as e:
            if e.status == 404:
                raise GistError(f"Gist {gist_id} not found")
            raise GistError(f"Failed to delete Gist: {e}")
        except Exception as e:
            raise GistError(f"Unexpected error deleting Gist: {e}")


# Global Gist manager instance
gist_manager = GistManager()

