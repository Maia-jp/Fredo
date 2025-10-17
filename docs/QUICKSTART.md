# Fredo Quick Start Guide

Get up and running with Fredo in 5 minutes!

## Installation

### From GitHub (Recommended)

```bash
pip3 install git+https://github.com/yourusername/fredo.git
```

### From Local Directory

```bash
cd /path/to/fredo
pip3 install -e .
```

### Verify

```bash
fredo init
fredo list
```

**That's it!** Now you can use `fredo` from anywhere in your terminal.

## Initialize

```bash
fredo init
```

This creates:
- Database: `~/.local/share/fredo/snippets.db`
- Config: `~/.config/fredo/config.toml`

## Basic Usage

### 1. Add Your First Snippet

```bash
fredo add hello --lang python --tag example
```

Your editor will open. Add this content:
```python
print("Hello from Fredo!")
```
Save and close.

### 2. View Your Snippet

```bash
fredo show hello
```

### 3. Run Your Snippet

```bash
fredo run hello
```

### 4. List All Snippets

```bash
fredo list
```

### 5. Search Snippets

```bash
# Interactive search (fuzzy finder)
fredo search

# Or search with a query
fredo search hello
```

## Next Steps

### Add More Snippets

```bash
# Bash script
fredo add backup --lang bash --tag utility

# JavaScript
fredo add test-api --lang javascript --tag api
```

### Organize with Tags

```bash
# Add tags to existing snippet
fredo tag add hello tutorial

# View all tags
fredo tag list
```

### Configure Editor

```bash
# Set your preferred editor
fredo config set editor "code --wait"  # VS Code
# or
fredo config set editor "vim"          # Vim
```

### GitHub Gist Integration (Optional)

```bash
# Setup (you'll need a GitHub personal access token)
fredo gist setup --token YOUR_TOKEN

# Backup all snippets
fredo gist sync

# Share a snippet
fredo share hello
```

## Common Commands

```bash
fredo add <name>         # Create new snippet
fredo edit <name>        # Edit snippet
fredo show <name>        # View snippet
fredo run <name>         # Execute snippet
fredo delete <name>      # Delete snippet
fredo list               # List all snippets
fredo search             # Interactive search
fredo tag list           # Show all tags
```

## Tips

1. **Use meaningful names**: `backup-postgres` instead of `script1`
2. **Tag consistently**: Use tags like `backup`, `deploy`, `utility`
3. **Add shebangs**: Start bash scripts with `#!/bin/bash`
4. **Search often**: The fuzzy search is your friend
5. **Backup regularly**: Use `fredo gist sync` to backup to GitHub

## Getting Help

```bash
# General help
fredo --help

# Command-specific help
fredo add --help
fredo run --help
```

## What's Next?

- Read [README.md](../README.md) for full documentation
- Check [EXAMPLES.md](EXAMPLES.md) for practical examples
- Start building your snippet library!

Happy coding with Fredo! 🎬

