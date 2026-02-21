"""Navigation commands."""

from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json

app = typer.Typer()


@app.command()
def goto(
    url: str,
    wait_until: str = typer.Option("networkidle", help="Wait until state: load, domcontentloaded, networkidle, commit"),
    timeout: int = typer.Option(60000, help="Timeout in milliseconds"),
    wait_for: Optional[str] = typer.Option(None, help="Wait for selector before completing"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Navigate to a URL.

    Navigate the browser to the specified URL and wait for the page to load.

    Examples:
        cli.py navigate goto https://example.com
        cli.py navigate goto https://example.com --wait-until networkidle
        cli.py navigate goto https://example.com --wait-for ".content"
    """

    async def _goto():
        connection = await get_connection(session_id, headless)
        await connection.page.goto(url, timeout=timeout, wait_until=wait_until)

        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=timeout)

        output_json(
            {
                "url": connection.page.url,
                "title": await connection.page.title(),
            }
        )

    run_async(_goto())


@app.command()
def back(
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Go back to the previous page."""

    async def _back():
        connection = await get_connection(session_id, headless)
        await connection.page.go_back()
        output_json(
            {
                "url": connection.page.url,
                "title": await connection.page.title(),
            }
        )

    run_async(_back())


@app.command()
def forward(
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Go forward to the next page."""

    async def _forward():
        connection = await get_connection(session_id, headless)
        await connection.page.go_forward()
        output_json(
            {
                "url": connection.page.url,
                "title": await connection.page.title(),
            }
        )

    run_async(_forward())


@app.command()
def reload(
    hard: bool = typer.Option(False, "--hard/--soft", help="Hard reload (bypass cache)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Reload the current page."""

    async def _reload():
        connection = await get_connection(session_id, headless)
        await connection.page.reload(wait_until="networkidle")
        output_json(
            {
                "url": connection.page.url,
                "title": await connection.page.title(),
            }
        )

    run_async(_reload())
