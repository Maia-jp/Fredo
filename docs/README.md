# Fredo Documentation

Welcome to the Fredo documentation! Here you'll find everything you need to get started and master Fredo.

## 📚 Documentation Index

### Getting Started

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Installation Guide](INSTALL.md)** - Detailed installation instructions for different environments

### Usage

- **[Examples](EXAMPLES.md)** - Real-world usage examples and best practices

## 🎯 Quick Links

- [Main README](../README.md) - Project overview and features
- [Contributing](../CONTRIBUTING.md) - How to contribute to Fredo
- [License](../LICENSE) - MIT License

## 📖 Core Concepts

### Snippets

Snippets are code fragments stored in Fredo. Each snippet has:
- **Name** - Unique identifier
- **Content** - The actual code
- **Language** - Programming language (auto-detected or specified)
- **Tags** - Labels for organization
- **Execution Mode** - How the snippet runs (current directory or isolated)

### Local-First Design

Fredo stores everything locally in a SQLite database at `~/.local/share/fredo/snippets.db`. This means:
- ⚡ Fast access
- 🔒 Your data stays private
- 📡 Works offline
- 🌐 Optional cloud sync via GitHub Gists

### Execution Modes

**Current Mode** (default)
- Runs in your current working directory
- Has access to local files and environment
- Best for trusted scripts

**Isolated Mode**
- Runs in a temporary directory
- Safer for untrusted code
- Automatically cleans up after execution

## 🔧 Configuration

Fredo uses a TOML configuration file at `~/.config/fredo/config.toml`:

```toml
database_path = "~/.local/share/fredo/snippets.db"
editor = "vim"
github_token = null
default_execution_mode = "current"
gist_private_by_default = true
```

## 🌟 Key Features

### Fuzzy Search

Fredo's fuzzy search helps you find snippets quickly:
- Search by name, content, tags
- Interactive TUI with real-time filtering
- CLI mode for scripts and automation

### Tag System

Organize snippets with multiple tags:
```bash
fredo add deploy --lang bash --tag deployment --tag production
fredo tag add deploy critical
fredo list --tag production
```

### GitHub Gist Integration

Backup and share snippets:
- Private gists by default
- Bidirectional sync
- Conflict detection
- Share with URL copying

## 🚀 Advanced Usage

### Running Snippets in Scripts

```bash
# Use in shell scripts
if fredo run health-check; then
    echo "System healthy"
else
    echo "System has issues"
fi
```

### Chaining Commands

```bash
# Run multiple snippets
fredo run build && fredo run test && fredo run deploy
```

### Export and Backup

```bash
# Backup all snippets to GitHub
fredo gist sync

# View raw snippet content
fredo show my-script --raw > backup.txt
```

## 🤔 Need Help?

- 📖 Check the [Examples](EXAMPLES.md) for common use cases
- 🐛 [Report a bug](https://github.com/yourusername/fredo/issues)
- 💡 [Request a feature](https://github.com/yourusername/fredo/issues)
- 📧 Contact the maintainers

## 🔄 Stay Updated

Watch the repository for updates and new features!

---

**Happy coding with Fredo!** 🎬

