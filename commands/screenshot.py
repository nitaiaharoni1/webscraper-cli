"""Screenshot commands."""

from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json

app = typer.Typer()


@app.command()
def capture(
    filename: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    selector: Optional[str] = typer.Option(None, help="CSS selector for element screenshot"),
    full_page: bool = typer.Option(False, "--full-page/--viewport", help="Take full page screenshot"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Take a screenshot."""

    async def _capture():
        connection = await get_connection(session_id, headless, url)

        if selector:
            await connection.page.locator(selector).first.screenshot(path=filename)
        else:
            await connection.page.screenshot(path=filename, full_page=full_page)

        output_json({"message": f"Screenshot saved to {filename}"})

    run_async(_capture())


@app.command()
def element(
    selector: str,
    filename: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Take a screenshot of a specific element."""

    async def _element():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first
        if await locator.count() == 0:
            output_json({"error": f"Element not found: {selector}"})
            return

        await locator.screenshot(path=filename)
        output_json({"message": f"Element screenshot saved to {filename}"})

    run_async(_element())


@app.command()
def visual_diff(
    image1: str,
    image2: str,
    output: str = typer.Option("diff.png", help="Output diff image path"),
    threshold: float = typer.Option(0.1, help="Difference threshold (0-1)"),
):
    """Compare two screenshots and generate a visual diff."""
    try:
        from PIL import Image, ImageChops
    except ImportError as e:
        output_json({"error": f"Required library not installed: {str(e)}. Run: pip install Pillow"})
        return

    try:
        img1 = Image.open(image1)
        img2 = Image.open(image2)

        if img1.size != img2.size:
            output_json({"error": f"Images have different sizes: {img1.size} vs {img2.size}"})
            return

        diff = ImageChops.difference(img1, img2)

        # Calculate difference percentage using Pillow (no numpy needed)
        diff_data = list(diff.getdata())
        total_values = len(diff_data) * len(diff_data[0]) if diff_data else 1
        diff_values = sum(1 for pixel in diff_data for c in pixel if c != 0)
        diff_percentage = (diff_values / total_values) * 100

        # Enhance diff for visibility
        diff = diff.convert("RGB")
        pixels = diff.load()
        width, height = diff.size

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]  # type: ignore[reportGeneralClassIssues]
                if r > threshold * 255 or g > threshold * 255 or b > threshold * 255:
                    pixels[x, y] = (255, 0, 0)
                else:
                    pixels[x, y] = (r, g, b)

        diff.save(output)

        output_json(
            {
                "message": f"Visual diff saved to {output}",
                "difference_percentage": round(diff_percentage, 2),
                "images_match": diff_percentage < threshold * 100,
            }
        )

    except FileNotFoundError as e:
        output_json({"error": f"Image file not found: {e}"})
    except Exception as e:
        output_json({"error": f"Error processing images: {str(e)}"})


@app.command()
def pdf(
    filename: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    format: str = typer.Option("A4", help="Paper format: A4, Letter, Legal, etc."),
    landscape: bool = typer.Option(False, "--landscape/--portrait", help="Use landscape orientation"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Save page as PDF (Chromium only)."""

    async def _pdf():
        connection = await get_connection(session_id, headless, url)

        # Check if browser is Chromium
        browser_name = connection.browser.browser_type.name if connection.browser else "chromium"
        if browser_name != "chromium":
            output_json({"error": "PDF generation is only supported in Chromium browsers"})
            return

        await connection.page.pdf(
            path=filename,
            format=format,
            landscape=landscape,
        )
        output_json({"message": f"PDF saved to {filename}"})

    run_async(_pdf())
