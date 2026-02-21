"""Browser emulation commands (device, viewport, geolocation)."""

from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json
from core.settings import settings

app = typer.Typer()


@app.command()
def device(
    device_name: str = typer.Argument(..., help="Device name (e.g., iPhone 14, iPad Pro)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Emulate device (iPhone, iPad, etc.)."""
    from playwright.async_api import async_playwright

    async def _emulate():
        connection = await get_connection(session_id, headless)
        try:
            # Get device from Playwright's device registry
            playwright = await async_playwright().start()
            try:
                devices_dict = playwright.devices
                device = devices_dict.get(device_name)
                if not device:
                    available = list(devices_dict.keys())[:10]
                    output_json({"error": f"Device not found. Available: {available}..."})
                    return

                await connection.page.set_viewport_size(device["viewport"])
                if "userAgent" in device:
                    await connection.context.set_extra_http_headers({"User-Agent": device["userAgent"]})

                if url:
                    await connection.page.goto(url, wait_until="domcontentloaded", timeout=settings.timeout)

                output_json({"message": f"Emulating {device_name}", "viewport": device["viewport"]})
            finally:
                await playwright.stop()
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_emulate())


@app.command()
def viewport(
    width: int = typer.Option(1280, help="Viewport width"),
    height: int = typer.Option(720, help="Viewport height"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Set viewport size."""

    async def _viewport():
        connection = await get_connection(session_id, headless)
        try:
            await connection.page.set_viewport_size({"width": width, "height": height})

            if url:
                await connection.page.goto(url, wait_until="domcontentloaded", timeout=settings.timeout)

            output_json({"message": f"Viewport set to {width}x{height}"})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_viewport())


@app.command()
def geolocation(
    latitude: float = typer.Option(..., "--lat", help="Latitude"),
    longitude: float = typer.Option(..., "--lon", help="Longitude"),
    accuracy: float = typer.Option(100, help="Accuracy in meters"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Set geolocation."""

    async def _geolocation():
        connection = await get_connection(session_id, headless)
        try:
            await connection.context.grant_permissions(["geolocation"])
            await connection.context.set_geolocation(
                {"latitude": latitude, "longitude": longitude, "accuracy": accuracy}
            )

            if url:
                await connection.page.goto(url, wait_until="domcontentloaded", timeout=settings.timeout)

            output_json({"message": f"Geolocation set to {latitude}, {longitude}"})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_geolocation())


@app.command()
def responsive(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to test"),
    output_dir: str = typer.Option("screenshots", help="Output directory for screenshots"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Take screenshots at multiple viewport sizes (mobile, tablet, desktop)."""
    from pathlib import Path

    async def _responsive():
        connection = await get_connection(session_id, headless, url)

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Define viewports
        viewports = {
            "mobile": {"width": 375, "height": 667},
            "mobile-landscape": {"width": 667, "height": 375},
            "tablet": {"width": 768, "height": 1024},
            "tablet-landscape": {"width": 1024, "height": 768},
            "desktop": {"width": 1920, "height": 1080},
            "desktop-small": {"width": 1366, "height": 768},
        }

        screenshots = []

        for name, viewport in viewports.items():
            await connection.page.set_viewport_size(viewport)
            filename = f"{output_dir}/{name}.png"
            await connection.page.screenshot(path=filename, full_page=True)
            screenshots.append({"name": name, "viewport": viewport, "file": filename})

        output_json(
            {"message": "Responsive screenshots captured", "screenshots": screenshots, "url": connection.page.url}
        )

    run_async(_responsive())


@app.command()
def dark_mode(
    enable: bool = typer.Option(True, help="Enable or disable dark mode"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Toggle prefers-color-scheme (dark/light mode)."""

    async def _dark_mode():
        connection = await get_connection(session_id, headless)

        color_scheme = "dark" if enable else "light"
        await connection.page.emulate_media(color_scheme=color_scheme)

        output_json({"message": f"Color scheme set to {color_scheme}", "color_scheme": color_scheme})

        if url:
            await connection.page.goto(url, wait_until="domcontentloaded")
            output_json({"message": f"Navigated to {url} with {color_scheme} mode"})

    run_async(_dark_mode())


@app.command()
def reduced_motion(
    enable: bool = typer.Option(True, help="Enable or disable reduced motion"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Toggle prefers-reduced-motion."""

    async def _reduced_motion():
        connection = await get_connection(session_id, headless)

        reduced_motion = "reduce" if enable else "no-preference"

        # Set via CDP
        cdp = await connection.context.new_cdp_session(connection.page)
        await cdp.send(
            "Emulation.setEmulatedMedia", {"features": [{"name": "prefers-reduced-motion", "value": reduced_motion}]}
        )

        output_json({"message": f"Reduced motion set to {reduced_motion}", "prefers_reduced_motion": reduced_motion})

        if url:
            await connection.page.goto(url, wait_until="domcontentloaded")
            output_json({"message": f"Navigated to {url} with reduced motion {reduced_motion}"})

    run_async(_reduced_motion())


@app.command()
def print_preview(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    output: Optional[str] = typer.Option(None, help="Save as PDF"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Trigger print media emulation."""

    async def _print_preview():
        connection = await get_connection(session_id, headless, url)

        # Emulate print media
        await connection.page.emulate_media(media="print")

        output_json({"message": "Print media emulation enabled", "url": connection.page.url})

        if output:
            await connection.page.pdf(path=output)
            output_json({"message": f"PDF saved to {output}"})

    run_async(_print_preview())


@app.command()
def contrast(
    enable: bool = typer.Option(True, help="Enable or disable high contrast"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Toggle prefers-contrast (high/no-preference)."""

    async def _contrast():
        connection = await get_connection(session_id, headless)

        contrast_value = "more" if enable else "no-preference"

        # Set via CDP
        cdp = await connection.context.new_cdp_session(connection.page)
        await cdp.send(
            "Emulation.setEmulatedMedia", {"features": [{"name": "prefers-contrast", "value": contrast_value}]}
        )

        output_json({"message": f"Contrast preference set to {contrast_value}", "prefers_contrast": contrast_value})

        if url:
            await connection.page.goto(url, wait_until="domcontentloaded")
            output_json({"message": f"Navigated to {url}"})

    run_async(_contrast())
