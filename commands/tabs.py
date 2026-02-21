"""Tab and history management commands."""

from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json

app = typer.Typer()


@app.command()
def open(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to open in new tab"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Open a new tab."""

    async def _open_tab():
        connection = await get_connection(session_id, headless)

        # Create new page
        new_page = await connection.context.new_page()

        if url:
            await new_page.goto(url, wait_until="domcontentloaded")

        # Get all pages
        pages = connection.context.pages

        output_json(
            {"message": "New tab opened", "url": new_page.url if url else "about:blank", "total_tabs": len(pages)}
        )

    run_async(_open_tab())


@app.command()
def close(
    index: Optional[int] = typer.Option(None, help="Tab index to close (0-based)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Close a tab."""

    async def _close_tab():
        connection = await get_connection(session_id, headless)

        pages = connection.context.pages

        if len(pages) <= 1:
            output_json({"error": "Cannot close the last tab"})
            return

        if index is not None:
            if 0 <= index < len(pages):
                await pages[index].close()
                output_json({"message": f"Closed tab {index}", "remaining_tabs": len(connection.context.pages)})
            else:
                output_json({"error": f"Invalid tab index: {index}"})
        else:
            # Close current page
            await connection.page.close()
            output_json({"message": "Closed current tab", "remaining_tabs": len(connection.context.pages)})

    run_async(_close_tab())


@app.command()
def switch(
    index: int = typer.Argument(..., help="Tab index to switch to (0-based)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Switch to a different tab."""

    async def _switch_tab():
        connection = await get_connection(session_id, headless)

        pages = connection.context.pages

        if 0 <= index < len(pages):
            target_page = pages[index]
            await target_page.bring_to_front()

            output_json(
                {"message": f"Switched to tab {index}", "url": target_page.url, "title": await target_page.title()}
            )
        else:
            output_json({"error": f"Invalid tab index: {index}. Total tabs: {len(pages)}"})

    run_async(_switch_tab())


@app.command()
def list(
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """List all open tabs."""

    async def _list_tabs():
        connection = await get_connection(session_id, headless)

        pages = connection.context.pages
        tabs_info = []

        for i, page in enumerate(pages):
            tabs_info.append(
                {"index": i, "url": page.url, "title": await page.title(), "is_current": page == connection.page}
            )

        output_json({"tabs": tabs_info, "total": len(tabs_info)})

    run_async(_list_tabs())
