"""Fredo - A CLI tool for managing and running code snippets.

This is a backward compatibility shim. The actual implementation
is in the fredo package.
"""

from fredo.main import app

if __name__ == "__main__":
    app()
