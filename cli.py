#!/usr/bin/env python3
"""Main CLI entry point for web scraping and automation tool."""

import sys
from typing import Optional

import typer

from commands import (
    api,
    audit,
    batch,
    clipboard,
    crawl,
    dialogs,
    docs,
    download,
    emulate,
    extract,
    frames,
    human,
    inspect,
    interact,
    navigate,
    network,
    record,
    shadow,
    storage,
    tabs,
    wait,
)
from commands import (
    eval as eval_module,
)
from commands import (
    screenshot as screenshot_module,
)
from core.progress import log_error
from core.settings import settings

app = typer.Typer(
    help="Powerful CLI tool for website scraping, automation, and crawling",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
    rich_markup_mode="rich",
    epilog="""
[bold]Quick Examples:[/bold]
  cli.py goto "https://example.com"
  cli.py text "h1" --url "https://example.com"
  cli.py click ".button" --url "https://example.com"
  cli.py capture page.png --url "https://example.com" --full-page

[bold]Documentation:[/bold]
  cli.py commands              List all available commands
  cli.py commands --format json    List commands in JSON format (for AI)
  cli.py help <command>       Show detailed help for a command
  cli.py help --category <cat>    Show all commands in a category

[bold]Command Categories:[/bold]
  Navigation:   navigate (goto, back, forward, reload)
  Extraction:   extract (text, links, html, table, markdown, meta, smart, xpath, regex)
  Interaction:  interact (click, type-text, hover, scroll, select, upload, fill-form)
  Screenshots:  screenshot (capture, element, visual-diff, pdf)
  Crawling:     crawl (site, sitemap, rss)
  Batch:        batch (urls, selectors, script, retry)
  Audits:       audit (a11y, seo, security, links, images, vitals, lighthouse)
  Network:      network (intercept, requests, throttle, offline, websocket)
  Emulation:    emulate (device, viewport, geolocation, dark-mode, responsive)
  API:          api (fetch, har, mock)
  Human-like:   human (type, mouse, drag)
  Inspection:   inspect (styles, bounds, contrast, fonts, sw)
  Recording:    record (start, stop, replay, video-start, video-stop)
  Tabs:         tabs (open, close, switch, list)
  And more...
""",
)


# Global options callback
@app.callback()
def global_options(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug information"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output except errors"),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json, csv, plain, table"),
    timeout: int = typer.Option(30000, "--timeout", help="Global timeout in milliseconds"),
    headless: bool = typer.Option(False, "--headless/--headed", help="Run in headless mode (default: headed/visible)"),
    proxy: Optional[str] = typer.Option(
        None, "--proxy", help="Proxy server (e.g., http://host:port, socks5://host:port)"
    ),
    user_agent: Optional[str] = typer.Option(None, "--user-agent", help="Custom User-Agent string"),
):
    """Global options for all commands."""
    settings.verbose = verbose
    settings.quiet = quiet
    settings.format = format
    settings.timeout = timeout
    settings.headless = headless
    settings.proxy = proxy
    settings.user_agent = user_agent


# Add command groups
app.add_typer(navigate.app, name="navigate", help="Navigation: goto, back, forward, reload")
app.add_typer(
    interact.app,
    name="interact",
    help="Interactions: click, type-text, hover, scroll, select, upload, fill-form, submit-form",
)
app.add_typer(
    extract.app,
    name="extract",
    help="Extraction: text, links, html, images, table, markdown, meta, schema, xpath, regex, smart, info, infinite, paginate",
)
app.add_typer(screenshot_module.app, name="screenshot", help="Screenshots: capture, element, visual-diff, pdf")
app.add_typer(wait.app, name="wait", help="Wait: selector, timeout, navigation, idle, animation")
app.add_typer(eval_module.app, name="eval", help="JavaScript: run")
app.add_typer(storage.app, name="storage", help="Storage: cookies, localstorage")
app.add_typer(batch.app, name="batch", help="Batch: urls, selectors, script, retry")
app.add_typer(crawl.app, name="crawl", help="Crawling: site, sitemap, rss")
app.add_typer(frames.app, name="frame", help="Frames: switch, main, list-frames")
app.add_typer(dialogs.app, name="dialog", help="Dialogs: accept, dismiss")
app.add_typer(clipboard.app, name="clipboard", help="Clipboard: copy, paste, select-text")
app.add_typer(download.app, name="download", help="Downloads: file, export, save-html")
app.add_typer(
    network.app, name="network", help="Network: intercept, requests, headers, auth, throttle, offline, websocket"
)
app.add_typer(
    emulate.app,
    name="emulate",
    help="Emulation: device, viewport, geolocation, responsive, dark-mode, reduced-motion, print-preview, contrast",
)
app.add_typer(shadow.app, name="shadow", help="Shadow DOM: access")
app.add_typer(api.app, name="api", help="API: fetch, har, mock")
app.add_typer(inspect.app, name="inspect", help="Inspection: styles, bounds, contrast, fonts, sw")
app.add_typer(human.app, name="human", help="Human-like: type, mouse, drag")
app.add_typer(
    audit.app, name="audit", help="Audits: a11y, seo, security, mixed, links, images, vitals, lighthouse, memory"
)
app.add_typer(record.app, name="record", help="Recording: start, stop, replay, video-start, video-stop, video-context")
app.add_typer(tabs.app, name="tabs", help="Tabs: open, close, switch, list")
app.add_typer(docs.app, name="docs", help="Documentation: commands, help, categories")


# Top-level shortcuts
@app.command()
def goto(
    url: str,
    wait_until: str = typer.Option(
        "domcontentloaded", help="Wait until state: load, domcontentloaded, networkidle, commit"
    ),
    timeout: Optional[int] = typer.Option(None, help="Timeout in milliseconds (overrides global)"),
    wait_for: Optional[str] = typer.Option(None, help="Wait for selector before completing"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
):
    """Navigate to a URL."""
    navigate.goto(url, wait_until, timeout or settings.timeout, wait_for, session_id, settings.headless)


@app.command()
def click(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    button: str = typer.Option("left", help="Mouse button: left, right, middle"),
    double: bool = typer.Option(False, "--double/--single", help="Perform double click"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
):
    """Click an element."""
    interact.click(selector, url, button, double, session_id, settings.headless)


@app.command()
def text(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    all: bool = typer.Option(False, "--all/--first", help="Extract from all matching elements"),
    format: Optional[str] = typer.Option(None, help="Output format: json, plain (overrides global)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
):
    """Extract text from elements."""
    extract.text(selector, url, all, format or settings.format, session_id, settings.headless)


@app.command()
def capture(
    filename: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    selector: Optional[str] = typer.Option(None, help="CSS selector for element screenshot"),
    full_page: bool = typer.Option(False, "--full-page/--viewport", help="Take full page screenshot"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
):
    """Take a screenshot (shortcut for screenshot capture)."""
    screenshot_module.capture(filename, url, selector, full_page, session_id, settings.headless)


@app.command(name="commands")
def commands_cmd(
    category: Optional[str] = typer.Option(None, help="Filter by category"),
    format: Optional[str] = typer.Option(None, help="Output format: json, table, markdown (overrides global)"),
):
    """List all available commands with descriptions and examples (shortcut for docs commands)."""
    docs.commands(category, format)


@app.command(name="help")
def help_cmd(
    command: Optional[str] = typer.Argument(None, help='Command name (e.g., "navigate goto" or "api fetch")'),
    category: Optional[str] = typer.Option(None, help="Show all commands in a category"),
):
    """Show detailed help for a command or category (shortcut for docs help)."""
    docs.help(command, category)


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        log_error(str(e))
        sys.exit(1)
