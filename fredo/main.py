"""Main entry point for Fredo CLI."""

import sys

from rich.console import Console

from fredo.cli.commands import app

console = Console()


def run():
    """Entry point for the CLI."""
    try:
        app(prog_name="fredo")
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        import traceback
        if "--debug" in sys.argv:
            traceback.print_exc()
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()

