"""Async execution helpers for CLI commands."""

import asyncio
import sys
from typing import Optional

from core.browser import BrowserConnection, get_or_create_connection, save_session_state
from core.errors import CLIError, NavigationError
from core.settings import settings


def run_async(coro):
    """Run an async coroutine from a sync typer command.

    Wraps asyncio.run() with consistent error handling so every command
    gets clean JSON error output instead of raw tracebacks.

    Usage:
        @app.command()
        def my_cmd(url: Optional[str] = ...):
            async def _inner():
                connection = await get_connection(session_id, headless, url)
                ...
            run_async(_inner())
    """
    try:
        asyncio.run(coro)
    except CLIError as e:
        _output_error(e.message, e.suggestion)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        msg = str(e)
        suggestion = _suggest_for_error(msg)
        _output_error(msg, suggestion)


async def get_connection(
    session_id: Optional[str] = None,
    headless: Optional[bool] = None,
    url: Optional[str] = None,
    wait_until: str = "domcontentloaded",
) -> BrowserConnection:
    """Get browser connection with optional URL navigation.

    Resolves headless from explicit param or global settings.
    Forwards proxy and user_agent from global settings.
    Navigates to URL if provided.
    """
    effective_headless = headless if headless is not None else settings.headless
    connection = await get_or_create_connection(
        session_id,
        headless=effective_headless,
        proxy=settings.proxy,
        user_agent=settings.user_agent,
    )

    if url:
        try:
            await connection.page.goto(url, wait_until=wait_until, timeout=settings.timeout)
        except Exception as e:
            # networkidle times out on SPAs with persistent background polling — fall back to load
            if wait_until == "networkidle" and "Timeout" in str(e):
                try:
                    await connection.page.wait_for_load_state("load", timeout=10000)
                except Exception:
                    pass  # Page is already loaded; background activity is fine
            else:
                raise NavigationError(url, str(e))

        # Persist session state so the next CLI invocation can restore it
        if session_id:
            await save_session_state(connection, session_id)

    return connection


def _output_error(message: str, suggestion: Optional[str] = None):
    """Output error as JSON and exit."""
    import json

    error = {"error": message}
    if suggestion:
        error["suggestion"] = suggestion
    print(json.dumps(error, indent=2), file=sys.stderr)
    sys.exit(1)


def _suggest_for_error(msg: str) -> Optional[str]:
    """Generate helpful suggestion based on error message."""
    msg_lower = msg.lower()
    if "net::err_name_not_resolved" in msg_lower:
        return "Check if the URL is correct and the domain exists."
    if "net::err_connection_refused" in msg_lower:
        return "The server refused the connection. Check if the URL and port are correct."
    if "net::err_proxy_connection_failed" in msg_lower:
        return "Proxy connection failed. Check your --proxy setting."
    if "timeout" in msg_lower:
        return "Try increasing --timeout or check if the page is accessible."
    if "element" in msg_lower and "not" in msg_lower:
        return "Check if the selector is correct or use --wait-for to wait for the element."
    if "chrome" in msg_lower and "not found" in msg_lower:
        return "Install Chrome or Chromium, or run: playwright install chromium"
    return None
