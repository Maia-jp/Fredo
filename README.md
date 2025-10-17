# 🎬 Fredo

A local-first CLI tool for managing and running code snippets with fuzzy search, GitHub Gist integration, and excellent developer UX.

## Features

- **📝 Snippet Management**: CRUD operations for code snippets
- **🔍 Fuzzy Search**: Interactive and CLI-based search with powerful filtering
- **🚀 Smart Execution**: Auto-detect language and run snippets with configurable modes
- **🏷️ Tagging System**: Organize snippets with tags
- **🌐 GitHub Gist Integration**: Backup, sync, and share snippets via Gist
- **💻 Editor Integration**: Edit snippets in your favorite editor (vim, emacs, vscode, etc.)
- **🎨 Beautiful UI**: Rich terminal output with syntax highlighting

## Installation

### One-Command Install from GitHub

```bash
pip3 install git+https://github.com/yourusername/fredo.git
```

That's it! Now you can use `fredo` from anywhere.

### Or Install from Local Directory

```bash
cd /path/to/fredo
pip3 install -e .
```

### Verify Installation

```bash
fredo init
fredo list
```

## Quick Start

```bash
# Initialize Fredo
fredo init

# Add your first snippet
fredo add hello --lang python --tag example
# (Your editor opens - add: print("Hello from Fredo!"))

# List snippets
fredo list

# Run your snippet
fredo run hello

# Search (interactive fuzzy finder)
fredo search
```

## Usage

### Core Commands

```bash
fredo add <name>           # Create new snippet
fredo edit <name>          # Edit snippet
fredo show <name>          # View snippet with syntax highlighting
fredo run <name>           # Execute snippet
fredo delete <name>        # Delete snippet
fredo list                 # List all snippets
fredo search [query]       # Search snippets (interactive or with query)
```

### Tag Management

```bash
fredo tag add <name> <tag>     # Add tag to snippet
fredo tag remove <name> <tag>  # Remove tag
fredo tag list                 # Show all tags
```

### GitHub Gist Integration

```bash
fredo gist setup --token YOUR_TOKEN   # Configure GitHub
fredo gist push <name>                # Push snippet to Gist
fredo gist pull <gist_id>             # Pull snippet from Gist  
fredo gist sync                       # Sync all snippets
fredo share <name>                    # Share snippet (copies URL)
```

### Configuration

```bash
fredo config show                      # Show configuration
fredo config set editor "code --wait"  # Set preferred editor
```

## Examples

### Python Script
```bash
fredo add backup-db --lang python --tag backup
# Add your backup script
fredo run backup-db
```

### Bash Script
```bash
fredo add docker-cleanup --lang bash --tag docker
# Add cleanup commands
fredo run docker-cleanup --mode isolated
```

### Search and Filter
```bash
# Interactive search
fredo search

# Search with query
fredo search docker

# Filter by language
fredo list --lang python

# Filter by tag
fredo list --tag backup
```

## Configuration

Config file: `~/.config/fredo/config.toml`

```toml
database_path = "~/.local/share/fredo/snippets.db"
editor = "vim"  # or null for auto-detect
github_token = "ghp_..."  # optional
default_execution_mode = "current"  # or "isolated"
gist_private_by_default = true
```

## Execution Modes

- **current**: Run snippet in current working directory
- **isolated**: Run snippet in temporary isolated directory (safer)

## Supported Languages

Auto-detects and runs: Python, Bash, JavaScript, TypeScript, Ruby, Go, Rust, PHP, Perl, Lua, R

## GitHub Gist Setup

1. Create Personal Access Token at https://github.com/settings/tokens
2. Select scope: `gist` (full control)
3. Configure: `fredo gist setup --token YOUR_TOKEN`
4. Backup: `fredo gist sync`

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - 5-minute getting started guide
- [EXAMPLES.md](EXAMPLES.md) - Practical real-world examples
- [INSTALL.md](INSTALL.md) - Detailed installation guide

## Philosophy

**Simple. Elegant. Rock-solid.**

- Local-first: Fast, no network dependency
- Developer-friendly: Amazing UX
- Clean code: Well-documented and maintainable

## Uninstall

```bash
pip3 uninstall fredo
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
