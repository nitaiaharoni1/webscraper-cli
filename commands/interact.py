"""Interaction commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager
from core import settings

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    print(json.dumps(data, indent=2))


@app.command()
def click(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    button: str = typer.Option('left', help='Mouse button: left, right, middle'),
    double: bool = typer.Option(False, '--double/--single', help='Perform double click'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Click an element."""
    import asyncio

    async def _click():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector).first

        if double:
            await locator.dblclick(button=button)
        else:
            await locator.click(button=button)

        output_json({'message': f'Clicked {selector}'})

    asyncio.run(_click())


@app.command()
def type_text(
    selector: str,
    text: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    delay: Optional[int] = typer.Option(None, help='Delay between keystrokes in milliseconds'),
    clear: bool = typer.Option(False, '--clear/--no-clear', help='Clear the field before typing'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Type text into an element."""
    import asyncio

    async def _type():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector).first

        if clear:
            await locator.clear()

        if delay:
            await locator.type(text, delay=delay)
        else:
            await locator.fill(text)

        output_json({'message': f'Typed text into {selector}'})

    asyncio.run(_type())


@app.command()
def hover(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Hover over an element."""
    import asyncio

    async def _hover():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        await connection.page.locator(selector).first.hover()
        output_json({'message': f'Hovered over {selector}'})

    asyncio.run(_hover())


@app.command()
def scroll(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    to: Optional[str] = typer.Option(None, help='Scroll to element matching selector'),
    by: Optional[int] = typer.Option(None, help='Scroll by number of pixels'),
    direction: str = typer.Option('down', help='Scroll direction: down, up'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Scroll the page."""
    import asyncio

    async def _scroll():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        if to:
            await connection.page.locator(to).first.scroll_into_view_if_needed()
            output_json({'message': f'Scrolled to {to}'})
        elif by:
            pixels = by if direction == 'down' else -by
            await connection.page.evaluate(f'window.scrollBy(0, {pixels})')
            output_json({'message': f'Scrolled {direction} by {abs(by)} pixels'})
        else:
            await connection.page.evaluate(
                f'window.scrollBy(0, window.innerHeight * {"1" if direction == "down" else "-1"})'
            )
            output_json({'message': f'Scrolled {direction}'})

    asyncio.run(_scroll())


@app.command()
def select(
    selector: str,
    value: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Select an option in a dropdown."""
    import asyncio

    async def _select():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector).first
        await locator.select_option(value)
        output_json({'message': f'Selected {value} in {selector}'})

    asyncio.run(_select())


@app.command()
def check(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Check a checkbox or radio button."""
    import asyncio

    async def _check():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector).first
        await locator.check()
        output_json({'message': f'Checked {selector}'})

    asyncio.run(_check())


@app.command()
def uncheck(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Uncheck a checkbox."""
    import asyncio

    async def _uncheck():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector).first
        await locator.uncheck()
        output_json({'message': f'Unchecked {selector}'})

    asyncio.run(_uncheck())


@app.command()
def press(
    key: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Press a keyboard key (e.g., Enter, Escape, Tab, ArrowDown)."""
    import asyncio

    async def _press():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        await connection.page.keyboard.press(key)
        output_json({'message': f'Pressed {key}'})

    asyncio.run(_press())


@app.command()
def focus(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Focus on an element."""
    import asyncio

    async def _focus():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector).first
        await locator.focus()
        output_json({'message': f'Focused on {selector}'})

    asyncio.run(_focus())


@app.command()
def drag(
    selector: str,
    target: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Drag an element to a target element."""
    import asyncio

    async def _drag():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        source_locator = connection.page.locator(selector).first
        target_locator = connection.page.locator(target).first
        await source_locator.drag_to(target_locator)
        output_json({'message': f'Dragged {selector} to {target}'})

    asyncio.run(_drag())


@app.command()
def upload(
    selector: str,
    file_path: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Upload a file to a file input."""
    import asyncio
    import os

    async def _upload():
        if not os.path.exists(file_path):
            output_json({'error': f'File not found: {file_path}'})
            return

        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector).first
            
        # Wait for file chooser and upload
        async with connection.page.expect_file_chooser() as fc_info:
            await locator.click()
        file_chooser = await fc_info.value
        await file_chooser.set_files(file_path)
            
        output_json({'message': f'Uploaded {file_path} to {selector}'})

    asyncio.run(_upload())


@app.command()
def keyboard(
    keys: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Press keyboard shortcuts (e.g., Control+C, Meta+V, Alt+Tab)."""
    import asyncio

    async def _keyboard():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        await connection.page.keyboard.press(keys)
        output_json({'message': f'Pressed keyboard shortcut: {keys}'})

    asyncio.run(_keyboard())


@app.command()
def select_option(
    selector: str,
    value: Optional[str] = typer.Option(None, help='Option value'),
    label: Optional[str] = typer.Option(None, help='Option label'),
    index: Optional[int] = typer.Option(None, help='Option index'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Select option from dropdown by value, label, or index."""
    import asyncio

    async def _select_option():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector).first
        
        if value:
            await locator.select_option(value=value)
            output_json({'message': f'Selected option by value: {value}'})
        elif label:
            await locator.select_option(label=label)
            output_json({'message': f'Selected option by label: {label}'})
        elif index is not None:
            await locator.select_option(index=index)
            output_json({'message': f'Selected option by index: {index}'})
        else:
            output_json({'error': 'Must provide value, label, or index'})

    asyncio.run(_select_option())


@app.command()
def pinch(
    scale: float = typer.Option(2.0, help='Pinch scale factor (>1 = zoom in, <1 = zoom out)'),
    x: Optional[int] = typer.Option(None, help='X coordinate (center if not provided)'),
    y: Optional[int] = typer.Option(None, help='Y coordinate (center if not provided)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Simulate pinch-to-zoom gesture (touch)."""
    import asyncio

    async def _pinch():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        # Get viewport center if coordinates not provided
        pinch_x = x
        pinch_y = y
        if pinch_x is None or pinch_y is None:
            viewport = connection.page.viewport_size
            if viewport:
                pinch_x = viewport['width'] // 2 if pinch_x is None else pinch_x
                pinch_y = viewport['height'] // 2 if pinch_y is None else pinch_y
            else:
                pinch_x = 500 if pinch_x is None else pinch_x
                pinch_y = 400 if pinch_y is None else pinch_y

        # Use CDP to simulate touch gestures
        cdp = await connection.context.new_cdp_session(connection.page)
        
        # Simulate pinch gesture
        await cdp.send('Input.synthesizePinchGesture', {
            'x': pinch_x,
            'y': pinch_y,
            'scaleFactor': scale,
            'relativeSpeed': 800,
            'gestureSourceType': 'touch'
        })
        
        output_json({
            'message': f'Pinch gesture executed',
            'scale': scale,
            'position': {'x': pinch_x, 'y': pinch_y}
        })

    asyncio.run(_pinch())
