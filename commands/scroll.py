"""Advanced scrolling commands (infinite scroll, pagination)."""

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
def infinite(
    extract: Optional[str] = typer.Option(None, '--extract', '-e', help='Selector to extract from each scroll'),
    max_items: int = typer.Option(100, help='Maximum items to extract'),
    scroll_delay: int = typer.Option(1000, help='Delay between scrolls (ms)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Auto-scroll infinite scroll pages and extract data."""
    import asyncio
    from core.progress import create_progress

    async def _infinite_scroll():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            items = []
            previous_count = 0
            no_change_count = 0

            with create_progress('Scrolling...') as progress:
                task = progress.add_task('Extracting items', total=None)
                
                while len(items) < max_items:
                    # Scroll to bottom
                    await connection.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await connection.page.wait_for_timeout(scroll_delay)
                    
                    # Extract items if selector provided
                    if extract:
                        current_items = await connection.page.evaluate(f'''
                            Array.from(document.querySelectorAll('{extract}'))
                                .map(el => el.textContent?.trim() || '')
                                .filter(text => text)
                        ''')
                        items = list(set(current_items))  # Remove duplicates
                    
                    # Check if we've reached the end
                    current_count = len(items)
                    if current_count == previous_count:
                        no_change_count += 1
                        if no_change_count >= 3:
                            break
                    else:
                        no_change_count = 0
                    
                    previous_count = current_count
                    progress.update(task, description=f'Found {len(items)} items')
                    
                    if len(items) >= max_items:
                        break

            output_json({'items': items[:max_items], 'count': len(items[:max_items])})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_infinite_scroll())


@app.command()
def paginate(
    next_selector: str = typer.Option(..., '--next', help='CSS selector of "next" button/link'),
    extract: Optional[str] = typer.Option(None, '--extract', '-e', help='Selector to extract from each page'),
    max_pages: int = typer.Option(10, help='Maximum pages to paginate'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Auto-paginate and extract data from multiple pages."""
    import asyncio
    from core.progress import create_progress

    async def _paginate():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            all_items = []
            page = 1

            with create_progress('Paginating...') as progress:
                task = progress.add_task('Pages processed', total=max_pages)
                
                while page <= max_pages:
                    # Extract items from current page
                    if extract:
                        items = await connection.page.evaluate(f'''
                            Array.from(document.querySelectorAll('{extract}'))
                                .map(el => el.textContent?.trim() || '')
                                .filter(text => text)
                        ''')
                        all_items.extend(items)
                    
                    # Check if next button exists
                    next_button = connection.page.locator(next_selector).first
                    if await next_button.count() == 0:
                        break
                    
                    # Check if next button is disabled
                    is_disabled = await next_button.evaluate('el => el.disabled || el.classList.contains("disabled")')
                    if is_disabled:
                        break
                    
                    # Click next button
                    await next_button.click()
                    await connection.page.wait_for_load_state('networkidle', timeout=settings.timeout)
                    
                    page += 1
                    progress.update(task, advance=1)

            output_json({'items': all_items, 'pages': page - 1, 'count': len(all_items)})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_paginate())
