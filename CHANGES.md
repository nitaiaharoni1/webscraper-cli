# Browser Behavior Update

## Changes Made

### Default Behavior
- **Headed mode (visible browser)** - Default, you can see what's happening
- **Browser stays open** - No restart overhead between commands
- Use `--headless` flag for invisible automation

### Benefits
1. **Visual feedback** - See what the browser is doing
2. **Faster execution** - No browser launch overhead between commands
3. **Session persistence** - Maintain cookies, localStorage, and page state
4. **Better for workflows** - Run multiple commands without restarts

### How It Works
- Browser launches on first command (visible by default)
- Stays open for subsequent commands
- Closes when process terminates (Ctrl+C) or Python exits
- Use `--headless` for invisible automation

### Examples

```bash
# Browser opens visibly and stays open (default)
python3 cli.py goto "https://example.com"

# Reuses same browser (fast!)
python3 cli.py text "h1"

# Still same browser
python3 cli.py extract links --format csv

# Run in headless mode (invisible, for automation)
python3 cli.py --headless batch urls urls.txt --concurrency 10

# Browser closes when you Ctrl+C or process exits
```

### Migration Notes
- Default is now headed (visible browser)
- Use `--headless` for invisible automation
- Commands run faster due to browser reuse
