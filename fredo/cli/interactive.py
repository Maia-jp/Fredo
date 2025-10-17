"""Interactive TUI for Fredo using prompt_toolkit."""

from typing import List, Optional

from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from fredo.core.database import db
from fredo.core.models import Snippet
from fredo.core.search import search_engine


class SnippetCompleter(Completer):
    """Custom completer for snippet fuzzy search."""

    def __init__(self):
        """Initialize the completer."""
        self.snippets: List[Snippet] = []
        self.refresh()

    def refresh(self):
        """Refresh the list of snippets."""
        self.snippets = db.list_all()

    def get_completions(self, document: Document, complete_event):
        """Get completions based on current input."""
        query = document.text

        # Search snippets
        if query:
            results = search_engine.search(query=query, limit=20)
        else:
            # Show all snippets if no query
            results = [type("R", (), {"snippet": s, "score": 100})() for s in self.snippets[:20]]

        for result in results:
            snippet = result.snippet
            # Format display text
            tags_str = f" [{', '.join(snippet.tags)}]" if snippet.tags else ""
            display = f"{snippet.name} ({snippet.language}){tags_str}"

            # Calculate display position
            start_position = -len(query)

            yield Completion(
                snippet.name,
                start_position=start_position,
                display=display,
                display_meta=snippet.content[:100] + "..." if len(snippet.content) > 100 else snippet.content,
            )


def fuzzy_select_snippet(
    message: str = "Select a snippet",
    language: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[Snippet]:
    """Show interactive fuzzy finder to select a snippet.

    Args:
        message: Prompt message
        language: Filter by language
        tags: Filter by tags

    Returns:
        Selected snippet or None if canceled
    """
    completer = SnippetCompleter()

    # If filters are provided, pre-filter snippets
    if language or tags:
        completer.snippets = db.search(language=language, tags=tags)

    try:
        # Show prompt with completer
        result = prompt(
            f"{message}: ",
            completer=completer,
            complete_while_typing=True,
        )

        if result:
            # Find snippet by name
            snippet = db.get_by_name(result)
            return snippet

        return None

    except (KeyboardInterrupt, EOFError):
        return None


def show_snippet_preview(snippet: Snippet) -> str:
    """Show a formatted preview of a snippet.

    Args:
        snippet: The snippet to preview

    Returns:
        Formatted preview string
    """
    # Format metadata
    tags_str = ", ".join(snippet.tags) if snippet.tags else "none"
    metadata = f"""
Name: {snippet.name}
Language: {snippet.language}
Tags: {tags_str}
Execution Mode: {snippet.execution_mode}
Updated: {snippet.updated_at.strftime('%Y-%m-%d %H:%M')}
"""

    # Syntax highlight content
    try:
        if snippet.language and snippet.language != "auto":
            lexer = get_lexer_by_name(snippet.language)
        else:
            from pygments.lexers import guess_lexer
            lexer = guess_lexer(snippet.content)

        highlighted = highlight(
            snippet.content,
            lexer,
            TerminalFormatter(),
        )
    except ClassNotFound:
        highlighted = snippet.content

    return f"{metadata}\nContent:\n{highlighted}"


def interactive_search(
    language: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[Snippet]:
    """Launch interactive search interface.

    Args:
        language: Filter by language
        tags: Filter by tags

    Returns:
        Selected snippet or None
    """
    return fuzzy_select_snippet(
        message="Search snippets (fuzzy)",
        language=language,
        tags=tags,
    )

