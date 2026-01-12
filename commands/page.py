"""Page information and PDF commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    print(json.dumps(data, indent=2))


@app.command()
def info(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Get page information (URL, title, viewport)."""
    import asyncio

    async def _info():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        viewport_size = connection.page.viewport_size
        info_data = {
            'url': connection.page.url,
            'title': await connection.page.title(),
            'viewport': {
                'width': viewport_size['width'] if viewport_size else None,
                'height': viewport_size['height'] if viewport_size else None,
            },
        }
        output_json(info_data)

    asyncio.run(_info())


@app.command()
def pdf(
    filename: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    format: str = typer.Option('A4', help='Paper format: A4, Letter, Legal, etc.'),
    landscape: bool = typer.Option(False, '--landscape/--portrait', help='Use landscape orientation'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Save page as PDF (Chromium only)."""
    import asyncio

    async def _pdf():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        # Check if browser is Chromium
        browser_name = connection.browser.browser_type.name if connection.browser else 'chromium'
        if browser_name != 'chromium':
            output_json({'error': 'PDF generation is only supported in Chromium browsers'})
            return

        await connection.page.pdf(
            path=filename,
            format=format,
            landscape=landscape,
        )
        output_json({'message': f'PDF saved to {filename}'})

    asyncio.run(_pdf())
