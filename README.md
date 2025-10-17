# 🎬 Fredo

> A local-first CLI tool for managing and running code snippets

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Fredo is a command-line tool that helps you organize, search, and run code snippets with ease. Store your scripts locally, find them with fuzzy search, and optionally sync them to GitHub Gists.

## ✨ Features

- 📝 **Snippet Management** - CRUD operations with a clean CLI
- 🔍 **Fuzzy Search** - Interactive TUI and CLI search with powerful filtering
- 🚀 **Smart Execution** - Auto-detects language and runs your snippets
- 🏷️ **Tag System** - Organize snippets with multiple tags
- 🌐 **GitHub Gist Sync** - Backup and share your snippets
- 💻 **Editor Integration** - Edit in vim, VS Code, or any editor
- 🎨 **Beautiful UI** - Rich terminal output with syntax highlighting
- ⚡ **Local-First** - Fast SQLite database, works offline

## 🚀 Quick Start

### Installation

```bash
pip3 install git+https://github.com/yourusername/fredo.git
```

### Basic Usage

```bash
# Initialize Fredo
fredo init

# Add a snippet (opens your editor)
fredo add hello --lang python --tag example

# List all snippets
fredo list

# Run a snippet
fredo run hello

# Interactive search
fredo search
```

## 📖 Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Get up and running in 5 minutes
- [Examples](docs/EXAMPLES.md) - Real-world usage examples
- [Installation Guide](docs/INSTALL.md) - Detailed installation instructions

## 🎯 Core Commands

| Command | Description |
|---------|-------------|
| `fredo add <name>` | Create a new snippet |
| `fredo edit <name>` | Edit an existing snippet |
| `fredo show <name>` | View a snippet with syntax highlighting |
| `fredo run <name>` | Execute a snippet |
| `fredo delete <name>` | Delete a snippet |
| `fredo list` | List all snippets |
| `fredo search [query]` | Search snippets (interactive or with query) |
| `fredo tag add <name> <tag>` | Add tags to a snippet |
| `fredo tag list` | List all tags |
| `fredo gist sync` | Sync all snippets to GitHub Gists |

## 💡 Usage Examples

### Python Script

```bash
fredo add backup-db --lang python --tag backup
# Editor opens, add your script
fredo run backup-db
```

### Bash Script

```bash
fredo add docker-cleanup --lang bash --tag docker --tag maintenance
# Add your cleanup commands
fredo run docker-cleanup --mode isolated
```

### Search and Filter

```bash
# Interactive fuzzy search
fredo search

# Search with query
fredo search docker

# Filter by language
fredo list --lang python

# Filter by tag
fredo list --tag backup
```

## 🔧 Configuration

Configuration is stored at `~/.config/fredo/config.toml`

```toml
database_path = "~/.local/share/fredo/snippets.db"
editor = "vim"  # or "code --wait", "nano", etc.
github_token = "ghp_..."  # optional
default_execution_mode = "current"  # or "isolated"
gist_private_by_default = true
```

### Set Your Editor

```bash
fredo config set editor "code --wait"  # VS Code
fredo config set editor "vim"          # Vim
```

## 🌐 GitHub Gist Integration

Backup and share your snippets with GitHub Gists:

```bash
# Setup (one-time)
fredo gist setup --token YOUR_GITHUB_TOKEN

# Push a snippet to Gist
fredo gist push my-script

# Pull from Gist
fredo gist pull GIST_ID

# Sync all snippets
fredo gist sync

# Share a snippet (copies URL to clipboard)
fredo share my-script
```

**Get GitHub Token:** https://github.com/settings/tokens (requires `gist` scope)

## 🏃 Execution Modes

- **current** - Run in your current working directory
- **isolated** - Run in a temporary isolated directory (safer for untrusted code)

```bash
# Override execution mode
fredo run my-script --mode isolated
```

## 🌍 Supported Languages

Auto-detects and executes:
- Python, Bash/Shell, JavaScript/Node.js, TypeScript
- Ruby, Go, Rust, PHP, Perl, Lua, R

Detection methods:
1. Explicit language flag (`--lang python`)
2. Shebang line (`#!/usr/bin/python3`)
3. Content analysis via Pygments

## 🛠️ Development

```bash
# Clone the repository
git clone https://github.com/yourusername/fredo.git
cd fredo

# Install in development mode
pip3 install -e .

# Run tests (if available)
pytest

# Make changes and they're immediately reflected
```

## 📋 Requirements

- Python 3.8 or higher
- pip3

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) - Interactive TUI
- [PyGithub](https://pygithub.readthedocs.io/) - GitHub API
- [Pygments](https://pygments.org/) - Syntax highlighting
- [TheFuzz](https://github.com/seatgeek/thefuzz) - Fuzzy search

## 🎯 Philosophy

**Simple. Elegant. Rock-solid.**

Fredo follows these principles:
- **Local-first** - Fast and works offline
- **Developer-friendly** - Intuitive commands and beautiful output
- **No over-engineering** - Clean, maintainable code

---

Made with ❤️ by developers, for developers

**[Documentation](docs/)** • **[Report Bug](https://github.com/yourusername/fredo/issues)** • **[Request Feature](https://github.com/yourusername/fredo/issues)**
