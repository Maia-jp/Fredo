"""CLI commands for Fredo."""

import sys
from typing import List, Optional

import typer
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from fredo.cli.interactive import fuzzy_select_snippet, interactive_search
from fredo.core.database import db
from fredo.core.models import Snippet, get_file_extension_for_language
from fredo.core.runner import runner
from fredo.core.search import search_engine
from fredo.integrations.gist import GistError, gist_manager
from fredo.utils.config import config_manager
from fredo.utils.editor import EditorError, editor_manager

app = typer.Typer(
    name="fredo",
    help="A CLI tool for managing and running code snippets",
    add_completion=False,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,
)
console = Console()


# ============================================================================
# Core CRUD Commands
# ============================================================================


@app.command()
def add(
    name: str = typer.Argument(..., help="Name of the snippet"),
    language: Optional[str] = typer.Option(
        None, "--lang", "-l", help="Language of the snippet"
    ),
    tags: Optional[List[str]] = typer.Option(
        None, "--tag", "-t", help="Tags for the snippet"
    ),
    execution_mode: str = typer.Option(
        "current", "--mode", "-m", help="Execution mode (current or isolated)"
    ),
):
    """Add a new snippet."""
    try:
        # Check if snippet already exists
        existing = db.get_by_name(name)
        if existing:
            console.print(f"[red]Error:[/red] Snippet '{name}' already exists")
            raise typer.Exit(1)

        # Determine file extension
        ext = get_file_extension_for_language(language) if language else ".txt"

        # Open editor
        content = editor_manager.edit_content(
            content="",
            extension=ext,
            message=f"Enter content for snippet '{name}'",
        )

        if not content or not content.strip():
            console.print("[yellow]Canceled:[/yellow] No content provided")
            raise typer.Exit(0)

        # Create snippet
        snippet = Snippet(
            name=name,
            content=content,
            language=language or "auto",
            tags=tags or [],
            execution_mode=execution_mode,
        )

        db.create(snippet)
        console.print(f"[green]✓[/green] Snippet '{name}' created successfully")

    except EditorError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def edit(
    name: str = typer.Argument(..., help="Name of the snippet to edit"),
):
    """Edit an existing snippet."""
    try:
        # Get snippet
        snippet = db.get_by_name(name)
        if not snippet:
            console.print(f"[red]Error:[/red] Snippet '{name}' not found")
            raise typer.Exit(1)

        # Open editor with current content
        ext = snippet.get_file_extension()
        content = editor_manager.edit_content(
            content=snippet.content,
            extension=ext,
            message=f"Editing snippet '{name}'",
        )

        if content is None or not content.strip():
            console.print("[yellow]Canceled:[/yellow] No changes made")
            raise typer.Exit(0)

        # Update snippet
        snippet.content = content
        db.update(snippet)
        console.print(f"[green]✓[/green] Snippet '{name}' updated successfully")

    except EditorError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def delete(
    name: str = typer.Argument(..., help="Name of the snippet to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a snippet."""
    try:
        # Get snippet
        snippet = db.get_by_name(name)
        if not snippet:
            console.print(f"[red]Error:[/red] Snippet '{name}' not found")
            raise typer.Exit(1)

        # Confirm deletion
        if not yes:
            confirm = typer.confirm(f"Delete snippet '{name}'?")
            if not confirm:
                console.print("[yellow]Canceled[/yellow]")
                raise typer.Exit(0)

        # Delete
        db.delete_by_name(name)
        console.print(f"[green]✓[/green] Snippet '{name}' deleted")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def show(
    name: str = typer.Argument(..., help="Name of the snippet to show"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Show raw content without formatting"),
):
    """Show a snippet."""
    try:
        # Get snippet
        snippet = db.get_by_name(name)
        if not snippet:
            console.print(f"[red]Error:[/red] Snippet '{name}' not found")
            raise typer.Exit(1)

        if raw:
            # Print raw content
            print(snippet.content)
        else:
            # Format and display
            tags_str = ", ".join(snippet.tags) if snippet.tags else "none"
            metadata = f"Language: {snippet.language} | Tags: {tags_str} | Mode: {snippet.execution_mode}"

            # Syntax highlight
            try:
                syntax = Syntax(
                    snippet.content,
                    snippet.language if snippet.language != "auto" else "text",
                    theme="monokai",
                    line_numbers=True,
                )
                panel = Panel(
                    syntax,
                    title=f"[bold]{snippet.name}[/bold]",
                    subtitle=metadata,
                    border_style="blue",
                )
                console.print(panel)
            except Exception:
                # Fallback to plain display
                console.print(f"\n[bold]{snippet.name}[/bold]")
                console.print(metadata)
                console.print(f"\n{snippet.content}\n")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="list")
def list_snippets(
    language: Optional[str] = typer.Option(None, "--lang", "-l", help="Filter by language"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """List all snippets."""
    try:
        # Get snippets
        if language or tag:
            tags = [tag] if tag else None
            snippets = db.search(language=language, tags=tags)
        else:
            snippets = db.list_all()

        if not snippets:
            console.print("[yellow]No snippets found[/yellow]")
            return

        # Create table
        table = Table(title="Snippets", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Language", style="green")
        table.add_column("Tags", style="yellow")
        table.add_column("Updated", style="dim")

        for snippet in snippets:
            tags_str = ", ".join(snippet.tags) if snippet.tags else "-"
            updated = snippet.updated_at.strftime("%Y-%m-%d %H:%M")
            table.add_row(snippet.name, snippet.language, tags_str, updated)

        console.print(table)
        console.print(f"\n[dim]Total: {len(snippets)} snippet(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def run(
    name: str = typer.Argument(..., help="Name of the snippet to run"),
    mode: Optional[str] = typer.Option(None, "--mode", "-m", help="Override execution mode"),
):
    """Run a snippet."""
    try:
        # Get snippet
        snippet = db.get_by_name(name)
        if not snippet:
            console.print(f"[red]Error:[/red] Snippet '{name}' not found")
            raise typer.Exit(1)

        # Override execution mode if specified
        if mode:
            snippet.execution_mode = mode

        # Detect language
        language = runner.detect_language(snippet)
        console.print(f"[dim]Running {snippet.name} ({language})...[/dim]\n")

        # Run snippet
        result = runner.run(snippet, capture_output=False)

        # Check exit code
        if result.returncode != 0:
            console.print(f"\n[red]✗[/red] Exited with code {result.returncode}")
            raise typer.Exit(result.returncode)
        else:
            console.print(f"\n[green]✓[/green] Completed successfully")

    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def search(
    query: Optional[str] = typer.Argument(None, help="Search query"),
    language: Optional[str] = typer.Option(None, "--lang", "-l", help="Filter by language"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    limit: Optional[int] = typer.Option(10, "--limit", "-n", help="Maximum results"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode"),
):
    """Search for snippets."""
    try:
        # If no query and not interactive, show interactive
        if not query and not interactive:
            snippet = interactive_search(
                language=language,
                tags=[tag] if tag else None,
            )
            if snippet:
                # Show the selected snippet
                ctx = typer.Context(show)
                ctx.invoke(show, name=snippet.name, raw=False)
            return

        # CLI search
        tags = [tag] if tag else None
        results = search_engine.search(
            query=query,
            language=language,
            tags=tags,
            limit=limit,
        )

        if not results:
            console.print("[yellow]No snippets found[/yellow]")
            return

        # Create table
        table = Table(title="Search Results", show_header=True, header_style="bold magenta")
        table.add_column("Score", style="cyan", justify="right", width=6)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Language", style="green")
        table.add_column("Tags", style="yellow")

        for result in results:
            snippet = result.snippet
            tags_str = ", ".join(snippet.tags) if snippet.tags else "-"
            table.add_row(
                str(result.score),
                snippet.name,
                snippet.language,
                tags_str,
            )

        console.print(table)
        console.print(f"\n[dim]Found: {len(results)} snippet(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# Tag Management Commands
# ============================================================================

tag_app = typer.Typer(help="Manage snippet tags")
app.add_typer(tag_app, name="tag")


@tag_app.command("add")
def tag_add(
    name: str = typer.Argument(..., help="Snippet name"),
    tags: List[str] = typer.Argument(..., help="Tags to add"),
):
    """Add tags to a snippet."""
    try:
        snippet = db.get_by_name(name)
        if not snippet:
            console.print(f"[red]Error:[/red] Snippet '{name}' not found")
            raise typer.Exit(1)

        # Add new tags
        existing_tags = set(snippet.tags)
        new_tags = set(tags)
        snippet.tags = list(existing_tags | new_tags)

        db.update(snippet)
        console.print(f"[green]✓[/green] Tags added to '{name}'")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@tag_app.command("remove")
def tag_remove(
    name: str = typer.Argument(..., help="Snippet name"),
    tags: List[str] = typer.Argument(..., help="Tags to remove"),
):
    """Remove tags from a snippet."""
    try:
        snippet = db.get_by_name(name)
        if not snippet:
            console.print(f"[red]Error:[/red] Snippet '{name}' not found")
            raise typer.Exit(1)

        # Remove tags
        snippet.tags = [t for t in snippet.tags if t not in tags]

        db.update(snippet)
        console.print(f"[green]✓[/green] Tags removed from '{name}'")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@tag_app.command("list")
def tag_list():
    """List all tags with counts."""
    try:
        tags = db.get_all_tags()

        if not tags:
            console.print("[yellow]No tags found[/yellow]")
            return

        # Create table
        table = Table(title="Tags", show_header=True, header_style="bold magenta")
        table.add_column("Tag", style="cyan")
        table.add_column("Count", style="green", justify="right")

        for tag, count in tags:
            table.add_row(tag, str(count))

        console.print(table)
        console.print(f"\n[dim]Total: {len(tags)} tag(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# GitHub Gist Commands
# ============================================================================

gist_app = typer.Typer(help="GitHub Gist integration")
app.add_typer(gist_app, name="gist")


@gist_app.command("setup")
def gist_setup(
    token: str = typer.Option(..., "--token", "-t", prompt=True, hide_input=True, help="GitHub personal access token"),
):
    """Configure GitHub token for Gist integration."""
    try:
        # Save token
        config_manager.set("github_token", token)

        # Test connection
        gist_manager.test_connection()

        console.print("[green]✓[/green] GitHub token configured successfully")

    except GistError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@gist_app.command("push")
def gist_push(
    name: str = typer.Argument(..., help="Snippet name"),
    public: bool = typer.Option(False, "--public", help="Make Gist public"),
):
    """Push a snippet to GitHub Gist."""
    try:
        snippet = db.get_by_name(name)
        if not snippet:
            console.print(f"[red]Error:[/red] Snippet '{name}' not found")
            raise typer.Exit(1)

        private = not public

        if snippet.gist_id:
            # Update existing Gist
            console.print(f"[dim]Updating existing Gist...[/dim]")
            gist = gist_manager.update_gist(snippet.gist_id, snippet)
        else:
            # Create new Gist
            console.print(f"[dim]Creating new Gist...[/dim]")
            gist = gist_manager.create_gist(snippet, private=private)

            # Update snippet with Gist info
            snippet.gist_id = gist.id
            snippet.gist_url = gist.html_url
            db.update(snippet)

        console.print(f"[green]✓[/green] Pushed to Gist: {gist.html_url}")

    except GistError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@gist_app.command("pull")
def gist_pull(
    gist_id: str = typer.Argument(..., help="Gist ID to pull"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Override snippet name"),
):
    """Pull a snippet from GitHub Gist."""
    try:
        # Get Gist
        console.print(f"[dim]Fetching Gist...[/dim]")
        gist = gist_manager.get_gist(gist_id)

        # Convert to snippet
        snippet = gist_manager.gist_to_snippet(gist)

        # Override name if provided
        if name:
            snippet.name = name

        # Check if snippet exists
        existing = db.get_by_name(snippet.name)
        if existing:
            confirm = typer.confirm(
                f"Snippet '{snippet.name}' already exists. Overwrite?"
            )
            if not confirm:
                console.print("[yellow]Canceled[/yellow]")
                raise typer.Exit(0)
            snippet.id = existing.id
            db.update(snippet)
        else:
            db.create(snippet)

        console.print(f"[green]✓[/green] Pulled snippet '{snippet.name}' from Gist")

    except GistError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@gist_app.command("sync")
def gist_sync(
    public: bool = typer.Option(False, "--public", help="Make Gists public"),
):
    """Sync all local snippets to GitHub Gist."""
    try:
        snippets = db.list_all()

        if not snippets:
            console.print("[yellow]No snippets to sync[/yellow]")
            return

        private = not public

        console.print(f"[dim]Syncing {len(snippets)} snippet(s)...[/dim]\n")

        for snippet in snippets:
            try:
                if snippet.gist_id:
                    gist = gist_manager.update_gist(snippet.gist_id, snippet)
                    console.print(f"[green]✓[/green] Updated: {snippet.name}")
                else:
                    gist = gist_manager.create_gist(snippet, private=private)
                    snippet.gist_id = gist.id
                    snippet.gist_url = gist.html_url
                    db.update(snippet)
                    console.print(f"[green]✓[/green] Created: {snippet.name}")
            except GistError as e:
                console.print(f"[red]✗[/red] Failed: {snippet.name} - {e}")

        console.print(f"\n[green]✓[/green] Sync complete")

    except GistError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@gist_app.command("share")
def gist_share(
    name: str = typer.Argument(..., help="Snippet name"),
):
    """Share a snippet via Gist and copy URL to clipboard."""
    try:
        snippet = db.get_by_name(name)
        if not snippet:
            console.print(f"[red]Error:[/red] Snippet '{name}' not found")
            raise typer.Exit(1)

        # Push to Gist (public)
        if snippet.gist_id:
            gist = gist_manager.update_gist(snippet.gist_id, snippet)
        else:
            gist = gist_manager.create_gist(snippet, private=False)
            snippet.gist_id = gist.id
            snippet.gist_url = gist.html_url
            db.update(snippet)

        # Try to copy to clipboard
        try:
            import subprocess
            subprocess.run(
                ["pbcopy"],
                input=gist.html_url.encode(),
                check=True,
            )
            console.print(f"[green]✓[/green] URL copied to clipboard: {gist.html_url}")
        except Exception:
            console.print(f"[green]✓[/green] Gist URL: {gist.html_url}")

    except GistError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# Configuration Commands
# ============================================================================

config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show():
    """Show current configuration."""
    try:
        config = config_manager.load()
        
        table = Table(title="Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Database Path", config.database_path)
        table.add_row("Editor", config.editor or "(auto-detect)")
        table.add_row("GitHub Token", "***" if config.github_token else "(not set)")
        table.add_row("Default Execution Mode", config.default_execution_mode)
        table.add_row("Gist Private by Default", str(config.gist_private_by_default))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
):
    """Set a configuration value."""
    try:
        config_manager.set(key, value)
        console.print(f"[green]✓[/green] Configuration updated: {key} = {value}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# Init Command
# ============================================================================


@app.command()
def init(
    reset: bool = typer.Option(False, "--reset", help="Reset database and configuration"),
):
    """Initialize Fredo (run on first use)."""
    try:
        if reset:
            confirm = typer.confirm("This will reset all data. Continue?")
            if not confirm:
                console.print("[yellow]Canceled[/yellow]")
                raise typer.Exit(0)

        # Initialize config
        config_manager.ensure_config_dir()
        config_manager.ensure_data_dir()
        config = config_manager.load()

        # Initialize database
        db.init_db()

        console.print("[green]✓[/green] Fredo initialized successfully")
        console.print(f"\n[dim]Database: {config.database_path}[/dim]")
        console.print(f"[dim]Config: {config_manager.config_file}[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

