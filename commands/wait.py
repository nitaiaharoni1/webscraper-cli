"""Wait commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    print(json.dumps(data, indent=2))


@app.command()
def selector(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    state: str = typer.Option('visible', help='Element state: visible, hidden, attached, detached'),
    timeout: int = typer.Option(30000, help='Timeout in milliseconds'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Wait for element matching selector."""
    import asyncio

    async def _wait_selector():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        await connection.page.wait_for_selector(selector, state=state, timeout=timeout)
        output_json({'message': f'Element {selector} is {state}'})

    asyncio.run(_wait_selector())


@app.command()
def timeout(
    milliseconds: int,
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Wait for specified duration."""
    import asyncio

    async def _wait_timeout():
        connection = await get_or_create_connection(session_id, headless=headless)
        await connection.page.wait_for_timeout(milliseconds)
        output_json({'message': f'Waited {milliseconds}ms'})

    asyncio.run(_wait_timeout())


@app.command()
def navigation(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    timeout: int = typer.Option(30000, help='Timeout in milliseconds'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Wait for page navigation."""
    import asyncio

    async def _wait_navigation():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        async with connection.page.expect_navigation(timeout=timeout):
            pass  # Wait for navigation triggered by page actions
        output_json({'message': 'Navigation completed', 'url': connection.page.url})

    asyncio.run(_wait_navigation())


@app.command()
def idle(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    timeout: int = typer.Option(30000, help='Timeout in milliseconds'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Wait for network idle (no network activity for 500ms)."""
    import asyncio

    async def _wait_idle():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='networkidle', timeout=timeout)
        else:
            await connection.page.wait_for_load_state('networkidle', timeout=timeout)
        
        output_json({'message': 'Network is idle', 'url': connection.page.url})

    asyncio.run(_wait_idle())


@app.command()
def animation(
    selector: Optional[str] = typer.Option(None, help='Wait for animations on specific element'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    duration: int = typer.Option(1000, help='Expected animation duration (ms)'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Wait for CSS animations to complete."""
    import asyncio

    async def _wait_animation():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        if selector:
            # Wait for animations on specific element
            await connection.page.evaluate(f'''
                async () => {{
                    const element = document.querySelector({json.dumps(selector)});
                    if (!element) return;
                    
                    const animations = element.getAnimations();
                    await Promise.all(animations.map(animation => animation.finished));
                }}
            ''')
        else:
            # Wait for all animations on page
            await connection.page.evaluate('''
                async () => {
                    const animations = document.getAnimations();
                    await Promise.all(animations.map(animation => animation.finished));
                }
            ''')
        
        # Additional buffer wait
        await connection.page.wait_for_timeout(duration)
        
        output_json({'message': 'Animations completed'})

    asyncio.run(_wait_animation())
