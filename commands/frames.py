"""Frame/iframe handling commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager
from core import settings

app = typer.Typer()

# Store current frame context per session
_frame_contexts: dict[str, str] = {}


def output_json(data: dict):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


@app.command()
def switch(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Switch to an iframe."""
    import asyncio

    async def _switch():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        effective_session_id = session_id or 'default'
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        frame_locator = connection.page.frame_locator(selector)
        _frame_contexts[effective_session_id] = selector
            
        # Verify frame exists
        frame = frame_locator.first
        output_json({'message': f'Switched to frame {selector}'})

    asyncio.run(_switch())


@app.command()
def main(
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Switch back to main frame."""
    import asyncio

    async def _main():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        effective_session_id = session_id or 'default'
        
        _frame_contexts[effective_session_id] = 'main'
        output_json({'message': 'Switched to main frame'})

    asyncio.run(_main())


@app.command()
def list_frames(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """List all frames on the page."""
    import asyncio

    async def _list():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        frames = await connection.page.evaluate('''
            Array.from(document.querySelectorAll('iframe'))
                .map((iframe, index) => ({
                    index: index,
                    src: iframe.src || '',
                    id: iframe.id || '',
                    name: iframe.name || '',
                    selector: iframe.id ? `#${iframe.id}` : iframe.name ? `[name="${iframe.name}"]` : `iframe:nth-of-type(${index + 1})`
                }))
        ''')
            
        output_json({'frames': frames})

    asyncio.run(_list())
