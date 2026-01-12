"""Screenshot commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    print(json.dumps(data, indent=2))


@app.command()
def capture(
    filename: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    selector: Optional[str] = typer.Option(None, help='CSS selector for element screenshot'),
    full_page: bool = typer.Option(False, '--full-page/--viewport', help='Take full page screenshot'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Take a screenshot."""
    import asyncio

    async def _screenshot():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        if selector:
            await connection.page.locator(selector).first.screenshot(path=filename)
        else:
            await connection.page.screenshot(path=filename, full_page=full_page)

        output_json({'message': f'Screenshot saved to {filename}'})

    asyncio.run(_screenshot())


@app.command()
def element(
    selector: str,
    filename: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Take a screenshot of a specific element."""
    import asyncio

    async def _element_screenshot():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector).first
        if await locator.count() == 0:
            output_json({'error': f'Element not found: {selector}'})
            return

        await locator.screenshot(path=filename)
        output_json({'message': f'Element screenshot saved to {filename}'})

    asyncio.run(_element_screenshot())


@app.command()
def fullpage(
    filename: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Take a full page screenshot (scrolling)."""
    import asyncio

    async def _fullpage_screenshot():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        await connection.page.screenshot(path=filename, full_page=True)
        output_json({'message': f'Full page screenshot saved to {filename}'})

    asyncio.run(_fullpage_screenshot())


@app.command()
def visual_diff(
    image1: str,
    image2: str,
    output: str = typer.Option('diff.png', help='Output diff image path'),
    threshold: float = typer.Option(0.1, help='Difference threshold (0-1)'),
):
    """Compare two screenshots and generate a visual diff."""
    try:
        from PIL import Image, ImageChops, ImageDraw
        import numpy as np
    except ImportError as e:
        output_json({'error': f'Required library not installed: {str(e)}. Run: pip install Pillow numpy'})
        return

    try:
        img1 = Image.open(image1)
        img2 = Image.open(image2)

        if img1.size != img2.size:
            output_json({'error': f'Images have different sizes: {img1.size} vs {img2.size}'})
            return

        diff = ImageChops.difference(img1, img2)
        
        # Calculate difference percentage
        diff_array = np.array(diff)
        total_pixels = diff_array.size
        diff_pixels = np.count_nonzero(diff_array)
        diff_percentage = (diff_pixels / total_pixels) * 100

        # Enhance diff for visibility
        diff = diff.convert('RGB')
        pixels = diff.load()
        width, height = diff.size
        
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                if r > threshold * 255 or g > threshold * 255 or b > threshold * 255:
                    pixels[x, y] = (255, 0, 0)  # Highlight differences in red
                else:
                    pixels[x, y] = (r, g, b)

        diff.save(output)
        
        output_json({
            'message': f'Visual diff saved to {output}',
            'difference_percentage': round(diff_percentage, 2),
            'images_match': diff_percentage < threshold * 100
        })

    except FileNotFoundError as e:
        output_json({'error': f'Image file not found: {e}'})
    except Exception as e:
        output_json({'error': f'Error processing images: {str(e)}'})
