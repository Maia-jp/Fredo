# Fredo Examples

This document provides practical examples for using Fredo.

## Getting Started

### 1. Initialize Fredo

```bash
fredo init
```

### 2. Create Your First Snippet

```bash
# Add a Python snippet
fredo add hello --lang python --tag example

# In the editor that opens, add:
print("Hello from Fredo!")
```

### 3. Run the Snippet

```bash
fredo run hello
```

## Common Use Cases

### Database Backup Script

```bash
# Create snippet
fredo add backup-postgres --lang bash --tag backup --tag database

# Add content (opens editor):
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump mydb > "backup_${DATE}.sql"
echo "Backup completed: backup_${DATE}.sql"

# Run it
fredo run backup-postgres
```

### API Testing Script

```bash
# Create snippet
fredo add test-api --lang python --tag api --tag testing

# Add content:
import requests

response = requests.get("https://api.github.com")
print(f"Status: {response.status_code}")
print(response.json())

# Run it
fredo run test-api
```

### Docker Cleanup

```bash
# Create snippet
fredo add docker-cleanup --lang bash --tag docker --tag maintenance

# Add content:
#!/bin/bash
echo "Cleaning up Docker..."
docker system prune -af
docker volume prune -f
echo "Cleanup complete!"

# Run in isolated mode (safer)
fredo run docker-cleanup --mode isolated
```

### Quick Math Calculator

```bash
# Create snippet
fredo add calc --lang python --tag utility

# Add content:
import sys
if len(sys.argv) > 1:
    print(eval(' '.join(sys.argv[1:])))
else:
    print("Usage: fredo run calc <expression>")

# Use it (note: be careful with eval in production)
fredo run calc "2 + 2"
```

## Search Examples

### Interactive Search

```bash
# Launch interactive fuzzy finder
fredo search

# Type to filter (e.g., "dock" will match "docker-cleanup")
# Use arrow keys to navigate
# Press Enter to select and view
```

### CLI Search

```bash
# Search for "backup" snippets
fredo search backup

# Search Python scripts
fredo search --lang python

# Search by tag
fredo search --tag api

# Combine filters
fredo search test --lang python --tag api --limit 5
```

## Tag Management

### Organizing with Tags

```bash
# Add multiple tags
fredo add deploy-prod --lang bash --tag deployment --tag production --tag critical

# Add tags to existing snippet
fredo tag add deploy-prod automated

# Remove a tag
fredo tag remove deploy-prod critical

# List all tags
fredo tag list
```

### Finding by Tags

```bash
# List all production snippets
fredo list --tag production

# Search within tagged snippets
fredo search deploy --tag production
```

## GitHub Gist Integration

### Setup

```bash
# Configure GitHub token
fredo gist setup --token ghp_your_token_here
```

### Backup All Snippets

```bash
# Sync all snippets to private Gists
fredo gist sync

# Sync as public Gists
fredo gist sync --public
```

### Share a Snippet

```bash
# Share a snippet (creates/updates Gist and copies URL)
fredo share my-script

# Now paste the URL in Slack, email, etc.
```

### Import from Gist

```bash
# Pull a Gist by ID
fredo gist pull abc123def456

# Pull with custom name
fredo gist pull abc123def456 --name my-imported-script
```

## Advanced Workflows

### Multi-Step Deployment

```bash
# Create multiple related snippets
fredo add deploy-build --lang bash --tag deploy
fredo add deploy-test --lang bash --tag deploy
fredo add deploy-push --lang bash --tag deploy

# Run them in sequence
fredo run deploy-build && fredo run deploy-test && fredo run deploy-push
```

### Template Snippet

```bash
# Create a template for new Python projects
fredo add python-template --lang python --tag template

# Content:
#!/usr/bin/env python3
"""
Module docstring
"""

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()

# Use it: show and copy
fredo show python-template --raw > new_script.py
```

### Quick Reference

```bash
# Create a reference snippet (not meant to be run)
fredo add git-commands --lang text --tag reference

# Content: common git commands
git checkout -b feature/new-branch
git commit -am "message"
git push origin feature/new-branch
git rebase -i HEAD~3

# View it quickly
fredo show git-commands
```

## Configuration Tips

### Set Your Preferred Editor

```bash
# Use VS Code
fredo config set editor "code --wait"

# Use vim
fredo config set editor "vim"

# Use nano
fredo config set editor "nano"
```

### Set Default Execution Mode

```bash
# Use isolated mode by default (safer)
fredo config set default_execution_mode isolated

# Use current directory by default
fredo config set default_execution_mode current
```

## Tips & Tricks

### 1. Quick Snippet Lookup
```bash
# Add aliases to your shell (~/.bashrc or ~/.zshrc)
alias fs='fredo search'
alias fr='fredo run'
alias fl='fredo list'
```

### 2. Integrate with Shell History
```bash
# Save a command from history as a snippet
# Run the command, then:
fc -ln -1 | xargs -I {} fredo add last-command --lang bash --tag quick
```

### 3. Use Shebangs for Clarity
Always start scripts with shebangs:
```bash
#!/bin/bash
# or
#!/usr/bin/env python3
```

### 4. Tag Consistently
Develop a tagging system:
- **Purpose**: `backup`, `deploy`, `test`, `monitor`
- **Environment**: `dev`, `staging`, `prod`
- **Language/Tool**: `docker`, `aws`, `git`
- **Priority**: `critical`, `important`, `nice-to-have`

### 5. Regular Backups
```bash
# Add to crontab for daily backups
0 2 * * * /path/to/fredo gist sync
```

## Troubleshooting

### Snippet Won't Run

```bash
# Check language detection
fredo show my-script

# Run with explicit mode
fredo run my-script --mode isolated

# Check if runtime is installed
which python3
which node
which bash
```

### Editor Won't Open

```bash
# Check editor configuration
fredo config show

# Set explicitly
fredo config set editor vim

# Or use environment variable
export EDITOR=vim
fredo edit my-script
```

### Gist Sync Fails

```bash
# Verify token
fredo gist setup --token your_new_token

# Check individual snippet
fredo gist push my-script
```

## More Examples

Check out the [Fredo repository](https://github.com/yourorg/fredo) for more examples and community-contributed snippets!

