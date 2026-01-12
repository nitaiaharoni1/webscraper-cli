"""Visual testing commands."""

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
def responsive(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to test'),
    output_dir: str = typer.Option('screenshots', help='Output directory for screenshots'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Take screenshots at multiple viewport sizes (mobile, tablet, desktop)."""
    import asyncio
    from pathlib import Path

    async def _responsive():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Define viewports
        viewports = {
            'mobile': {'width': 375, 'height': 667},
            'mobile-landscape': {'width': 667, 'height': 375},
            'tablet': {'width': 768, 'height': 1024},
            'tablet-landscape': {'width': 1024, 'height': 768},
            'desktop': {'width': 1920, 'height': 1080},
            'desktop-small': {'width': 1366, 'height': 768}
        }
        
        screenshots = []
        
        for name, viewport in viewports.items():
            await connection.page.set_viewport_size(viewport)
            filename = f'{output_dir}/{name}.png'
            await connection.page.screenshot(path=filename, full_page=True)
            screenshots.append({
                'name': name,
                'viewport': viewport,
                'file': filename
            })
        
        output_result({
            'message': 'Responsive screenshots captured',
            'screenshots': screenshots,
            'url': connection.page.url
        })

    asyncio.run(_responsive())


@app.command()
def dark_mode(
    enable: bool = typer.Option(True, help='Enable or disable dark mode'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Toggle prefers-color-scheme (dark/light mode)."""
    import asyncio

    async def _dark_mode():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        color_scheme = 'dark' if enable else 'light'
        await connection.page.emulate_media(color_scheme=color_scheme)
        
        output_result({
            'message': f'Color scheme set to {color_scheme}',
            'color_scheme': color_scheme
        })
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
            output_result({'message': f'Navigated to {url} with {color_scheme} mode'})

    asyncio.run(_dark_mode())


@app.command()
def reduced_motion(
    enable: bool = typer.Option(True, help='Enable or disable reduced motion'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Toggle prefers-reduced-motion."""
    import asyncio

    async def _reduced_motion():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        reduced_motion = 'reduce' if enable else 'no-preference'
        
        # Set via CDP
        cdp = await connection.context.new_cdp_session(connection.page)
        await cdp.send('Emulation.setEmulatedMedia', {
            'features': [{
                'name': 'prefers-reduced-motion',
                'value': reduced_motion
            }]
        })
        
        output_result({
            'message': f'Reduced motion set to {reduced_motion}',
            'prefers_reduced_motion': reduced_motion
        })
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
            output_result({'message': f'Navigated to {url} with reduced motion {reduced_motion}'})

    asyncio.run(_reduced_motion())


@app.command()
def print_preview(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    output: Optional[str] = typer.Option(None, help='Save as PDF'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Trigger print media emulation."""
    import asyncio

    async def _print_preview():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        # Emulate print media
        await connection.page.emulate_media(media='print')
        
        output_result({
            'message': 'Print media emulation enabled',
            'url': connection.page.url
        })
        
        if output:
            await connection.page.pdf(path=output)
            output_result({'message': f'PDF saved to {output}'})

    asyncio.run(_print_preview())


@app.command()
def viewport(
    width: int = typer.Option(..., help='Viewport width'),
    height: int = typer.Option(..., help='Viewport height'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Set custom viewport size."""
    import asyncio

    async def _viewport():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        await connection.page.set_viewport_size({'width': width, 'height': height})
        
        output_result({
            'message': f'Viewport set to {width}x{height}',
            'viewport': {'width': width, 'height': height}
        })
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
            output_result({'message': f'Navigated to {url}'})

    asyncio.run(_viewport())


@app.command()
def contrast(
    enable: bool = typer.Option(True, help='Enable or disable high contrast'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Toggle prefers-contrast (high/no-preference)."""
    import asyncio

    async def _contrast():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        contrast_value = 'more' if enable else 'no-preference'
        
        # Set via CDP
        cdp = await connection.context.new_cdp_session(connection.page)
        await cdp.send('Emulation.setEmulatedMedia', {
            'features': [{
                'name': 'prefers-contrast',
                'value': contrast_value
            }]
        })
        
        output_result({
            'message': f'Contrast preference set to {contrast_value}',
            'prefers_contrast': contrast_value
        })
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
            output_result({'message': f'Navigated to {url}'})

    asyncio.run(_contrast())
