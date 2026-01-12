"""Browser emulation commands (device, viewport, geolocation)."""

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
def device(
    device_name: str = typer.Argument(..., help='Device name (e.g., iPhone 14, iPad Pro)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Emulate device (iPhone, iPad, etc.)."""
    import asyncio
    from playwright.async_api import async_playwright

    async def _emulate():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            # Get device from Playwright's device registry
            playwright = await async_playwright().start()
            try:
                devices_dict = playwright.devices
                device = devices_dict.get(device_name)
                if not device:
                    available = list(devices_dict.keys())[:10]
                    output_json({'error': f'Device not found. Available: {available}...'})
                    return

                await connection.page.set_viewport_size(device['viewport'])
                if 'userAgent' in device:
                    await connection.context.set_extra_http_headers({'User-Agent': device['userAgent']})
                
                if url:
                    await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)
                
                output_json({'message': f'Emulating {device_name}', 'viewport': device['viewport']})
            finally:
                await playwright.stop()
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_emulate())


@app.command()
def viewport(
    width: int = typer.Option(1280, help='Viewport width'),
    height: int = typer.Option(720, help='Viewport height'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Set viewport size."""
    import asyncio

    async def _viewport():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            await connection.page.set_viewport_size({'width': width, 'height': height})
            
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)
            
            output_json({'message': f'Viewport set to {width}x{height}'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_viewport())


@app.command()
def geolocation(
    latitude: float = typer.Option(..., '--lat', help='Latitude'),
    longitude: float = typer.Option(..., '--lon', help='Longitude'),
    accuracy: float = typer.Option(100, help='Accuracy in meters'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Set geolocation."""
    import asyncio

    async def _geolocation():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            await connection.context.grant_permissions(['geolocation'])
            await connection.context.set_geolocation({
                'latitude': latitude,
                'longitude': longitude,
                'accuracy': accuracy
            })
            
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)
            
            output_json({'message': f'Geolocation set to {latitude}, {longitude}'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_geolocation())
