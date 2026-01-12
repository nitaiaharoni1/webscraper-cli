"""Tab and history management commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection
from core.settings import settings

app = typer.Typer()


def output_result(data):
    """Output data in the configured format."""
    if settings.format == 'json':
        print(json.dumps(data, indent=2))
    else:
        print(data)


@app.command()
def open(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to open in new tab'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Open a new tab."""
    import asyncio

    async def _open_tab():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        # Create new page
        new_page = await connection.context.new_page()
        
        if url:
            await new_page.goto(url, wait_until='domcontentloaded')
        
        # Get all pages
        pages = connection.context.pages
        
        output_result({
            'message': 'New tab opened',
            'url': new_page.url if url else 'about:blank',
            'total_tabs': len(pages)
        })

    asyncio.run(_open_tab())


@app.command()
def close(
    index: Optional[int] = typer.Option(None, help='Tab index to close (0-based)'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Close a tab."""
    import asyncio

    async def _close_tab():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        pages = connection.context.pages
        
        if len(pages) <= 1:
            output_result({'error': 'Cannot close the last tab'})
            return
        
        if index is not None:
            if 0 <= index < len(pages):
                await pages[index].close()
                output_result({
                    'message': f'Closed tab {index}',
                    'remaining_tabs': len(connection.context.pages)
                })
            else:
                output_result({'error': f'Invalid tab index: {index}'})
        else:
            # Close current page
            await connection.page.close()
            output_result({
                'message': 'Closed current tab',
                'remaining_tabs': len(connection.context.pages)
            })

    asyncio.run(_close_tab())


@app.command()
def switch(
    index: int = typer.Argument(..., help='Tab index to switch to (0-based)'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Switch to a different tab."""
    import asyncio

    async def _switch_tab():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        pages = connection.context.pages
        
        if 0 <= index < len(pages):
            target_page = pages[index]
            await target_page.bring_to_front()
            
            output_result({
                'message': f'Switched to tab {index}',
                'url': target_page.url,
                'title': await target_page.title()
            })
        else:
            output_result({'error': f'Invalid tab index: {index}. Total tabs: {len(pages)}'})

    asyncio.run(_switch_tab())


@app.command()
def list(
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """List all open tabs."""
    import asyncio

    async def _list_tabs():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        pages = connection.context.pages
        tabs_info = []
        
        for i, page in enumerate(pages):
            tabs_info.append({
                'index': i,
                'url': page.url,
                'title': await page.title(),
                'is_current': page == connection.page
            })
        
        output_result({
            'tabs': tabs_info,
            'total': len(tabs_info)
        })

    asyncio.run(_list_tabs())


@app.command()
def back(
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Navigate back in history."""
    import asyncio

    async def _back():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        try:
            await connection.page.go_back(wait_until='domcontentloaded')
            output_result({
                'message': 'Navigated back',
                'url': connection.page.url
            })
        except Exception as e:
            output_result({'error': f'Cannot go back: {str(e)}'})

    asyncio.run(_back())


@app.command()
def forward(
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Navigate forward in history."""
    import asyncio

    async def _forward():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        try:
            await connection.page.go_forward(wait_until='domcontentloaded')
            output_result({
                'message': 'Navigated forward',
                'url': connection.page.url
            })
        except Exception as e:
            output_result({'error': f'Cannot go forward: {str(e)}'})

    asyncio.run(_forward())


@app.command()
def history(
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Get browser history for current page."""
    import asyncio

    async def _history():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        # Get history via JavaScript
        history_data = await connection.page.evaluate('''
            () => {
                return {
                    length: window.history.length,
                    currentUrl: window.location.href,
                    state: window.history.state
                };
            }
        ''')
        
        output_result({
            'history': history_data,
            'note': 'Browser security prevents reading full history. Only length and current state available.'
        })

    asyncio.run(_history())
