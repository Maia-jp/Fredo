# Installation Guide

## Quick Install (1 Command)

```bash
cd /Users/joao/Developer/Misc/fredo && pip3 install -e .
```

After installation, verify it works:
```bash
fredo --help
```

## Step-by-Step Installation

### 1. Navigate to the Project

```bash
cd /Users/joao/Developer/Misc/fredo
```

### 2. Install the Package

```bash
pip3 install -e .
```

The `-e` flag means "editable" - any changes you make to the code will be reflected immediately.

### 3. Verify Installation

```bash
fredo --help
```

You should see:
```
Usage: fredo [OPTIONS] COMMAND [ARGS]...

A CLI tool for managing and running code snippets
...
```

### 4. Initialize Fredo

```bash
fredo init
```

This creates:
- Database: `~/.local/share/fredo/snippets.db`
- Config: `~/.config/fredo/config.toml`

## Troubleshooting

### Command not found: fredo

If you get "command not found", it means pip's bin directory isn't in your PATH.

**Solution 1: Add pip's bin directory to PATH**

Add this to your `~/.zshrc` (or `~/.bashrc` if using bash):

```bash
# For user-level pip installations
export PATH="$HOME/.local/bin:$PATH"

# For Homebrew Python
export PATH="/opt/homebrew/bin:$PATH"
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

**Solution 2: Use pipx (recommended for CLI tools)**

```bash
# Install pipx if you don't have it
brew install pipx
pipx ensurepath

# Install fredo with pipx
cd /Users/joao/Developer/Misc/fredo
pipx install -e .
```

**Solution 3: Use full path**

Find where pip installed it:
```bash
which python3
# Example: /opt/homebrew/bin/python3
```

The fredo script will be in the same directory or in `../bin/`.

### Permission denied

If you get permission errors:

```bash
# Use --user flag
pip3 install --user -e .
```

### Virtual environment

If you prefer using a virtual environment:

```bash
cd /Users/joao/Developer/Misc/fredo

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install
pip install -e .

# Now fredo is available (while venv is active)
fredo --help
```

## Uninstall

```bash
pip3 uninstall fredo
```

## Update

Since you installed in editable mode (`-e`), any code changes are automatically reflected. No need to reinstall!

If you want to reinstall from scratch:

```bash
pip3 uninstall fredo
pip3 install -e .
```

## Alternative: Use without Installing

If you don't want to install globally, you can always use:

```bash
cd /Users/joao/Developer/Misc/fredo
uv run fredo --help
```

Or:

```bash
cd /Users/joao/Developer/Misc/fredo
python3 -m fredo --help
```

