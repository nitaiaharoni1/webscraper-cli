"""Dialog handling commands (alert, confirm, prompt)."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager
from core import settings

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


@app.command()
def accept(
    text: Optional[str] = typer.Option(None, help='Text to enter (for prompt dialogs)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Accept a dialog (alert/confirm) or enter text (prompt)."""
    import asyncio

    async def _accept():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        # Set up dialog handler
        dialog_handled = {'accepted': False}
            
        def handle_dialog(dialog):
            dialog_handled['accepted'] = True
            if text:
                dialog.accept(text)
            else:
                dialog.accept()

        connection.page.on('dialog', handle_dialog)
            
        # Wait a bit for dialog to appear (or trigger action that shows dialog)
        await connection.page.wait_for_timeout(1000)
            
        output_json({'message': 'Dialog handler set up. Dialog will be accepted when it appears.'})

    asyncio.run(_accept())


@app.command()
def dismiss(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Dismiss a dialog."""
    import asyncio

    async def _dismiss():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        def handle_dialog(dialog):
            dialog.dismiss()

        connection.page.on('dialog', handle_dialog)
        await connection.page.wait_for_timeout(1000)
            
        output_json({'message': 'Dialog handler set up. Dialog will be dismissed when it appears.'})

    asyncio.run(_dismiss())
