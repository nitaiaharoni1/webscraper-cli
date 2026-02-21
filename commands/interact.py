"""Interaction commands."""

import json
import os
from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json
from core.settings import settings

app = typer.Typer()


@app.command()
def click(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    button: str = typer.Option("left", help="Mouse button: left, right, middle"),
    double: bool = typer.Option(False, "--double/--single", help="Perform double click"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Click an element."""

    async def _click():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first

        if double:
            await locator.dblclick(button=button)
        else:
            await locator.click(button=button)

        output_json({"message": f"Clicked {selector}"})

    run_async(_click())


@app.command()
def type_text(
    selector: str,
    text: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    delay: Optional[int] = typer.Option(None, help="Delay between keystrokes in milliseconds"),
    clear: bool = typer.Option(False, "--clear/--no-clear", help="Clear the field before typing"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Type text into an element."""

    async def _type():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first

        if clear:
            await locator.clear()

        if delay:
            await locator.type(text, delay=delay)
        else:
            await locator.fill(text)

        output_json({"message": f"Typed text into {selector}"})

    run_async(_type())


@app.command()
def hover(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Hover over an element."""

    async def _hover():
        connection = await get_connection(session_id, headless, url)

        await connection.page.locator(selector).first.hover()
        output_json({"message": f"Hovered over {selector}"})

    run_async(_hover())


@app.command()
def scroll(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    to: Optional[str] = typer.Option(None, help="Scroll to element matching selector"),
    by: Optional[int] = typer.Option(None, help="Scroll by number of pixels"),
    direction: str = typer.Option("down", help="Scroll direction: down, up"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Scroll the page."""

    async def _scroll():
        connection = await get_connection(session_id, headless, url)

        if to:
            await connection.page.locator(to).first.scroll_into_view_if_needed()
            output_json({"message": f"Scrolled to {to}"})
        elif by:
            pixels = by if direction == "down" else -by
            await connection.page.evaluate(f"window.scrollBy(0, {pixels})")
            output_json({"message": f"Scrolled {direction} by {abs(by)} pixels"})
        else:
            await connection.page.evaluate(
                f"window.scrollBy(0, window.innerHeight * {'1' if direction == 'down' else '-1'})"
            )
            output_json({"message": f"Scrolled {direction}"})

    run_async(_scroll())


@app.command()
def select(
    selector: str,
    value: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Select an option in a dropdown."""

    async def _select():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first
        await locator.select_option(value)
        output_json({"message": f"Selected {value} in {selector}"})

    run_async(_select())


@app.command()
def check(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Check a checkbox or radio button."""

    async def _check():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first
        await locator.check()
        output_json({"message": f"Checked {selector}"})

    run_async(_check())


@app.command()
def uncheck(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Uncheck a checkbox."""

    async def _uncheck():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first
        await locator.uncheck()
        output_json({"message": f"Unchecked {selector}"})

    run_async(_uncheck())


@app.command()
def press(
    key: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Press a keyboard key (e.g., Enter, Escape, Tab, ArrowDown)."""

    async def _press():
        connection = await get_connection(session_id, headless, url)

        await connection.page.keyboard.press(key)
        output_json({"message": f"Pressed {key}"})

    run_async(_press())


@app.command()
def focus(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Focus on an element."""

    async def _focus():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first
        await locator.focus()
        output_json({"message": f"Focused on {selector}"})

    run_async(_focus())


@app.command()
def drag(
    selector: str,
    target: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Drag an element to a target element."""

    async def _drag():
        connection = await get_connection(session_id, headless, url)

        source_locator = connection.page.locator(selector).first
        target_locator = connection.page.locator(target).first
        await source_locator.drag_to(target_locator)
        output_json({"message": f"Dragged {selector} to {target}"})

    run_async(_drag())


@app.command()
def upload(
    selector: str,
    file_path: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Upload a file to a file input."""
    import os

    async def _upload():
        if not os.path.exists(file_path):
            output_json({"error": f"File not found: {file_path}"})
            return

        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first

        # Wait for file chooser and upload
        async with connection.page.expect_file_chooser() as fc_info:
            await locator.click()
        file_chooser = await fc_info.value
        await file_chooser.set_files(file_path)

        output_json({"message": f"Uploaded {file_path} to {selector}"})

    run_async(_upload())


@app.command()
def keyboard(
    keys: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Press keyboard shortcuts (e.g., Control+C, Meta+V, Alt+Tab)."""

    async def _keyboard():
        connection = await get_connection(session_id, headless, url)

        await connection.page.keyboard.press(keys)
        output_json({"message": f"Pressed keyboard shortcut: {keys}"})

    run_async(_keyboard())


@app.command()
def select_option(
    selector: str,
    value: Optional[str] = typer.Option(None, help="Option value"),
    label: Optional[str] = typer.Option(None, help="Option label"),
    index: Optional[int] = typer.Option(None, help="Option index"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Select option from dropdown by value, label, or index."""

    async def _select_option():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first

        if value:
            await locator.select_option(value=value)
            output_json({"message": f"Selected option by value: {value}"})
        elif label:
            await locator.select_option(label=label)
            output_json({"message": f"Selected option by label: {label}"})
        elif index is not None:
            await locator.select_option(index=index)
            output_json({"message": f"Selected option by index: {index}"})
        else:
            output_json({"error": "Must provide value, label, or index"})

    run_async(_select_option())


@app.command()
def pinch(
    scale: float = typer.Option(2.0, help="Pinch scale factor (>1 = zoom in, <1 = zoom out)"),
    x: Optional[int] = typer.Option(None, help="X coordinate (center if not provided)"),
    y: Optional[int] = typer.Option(None, help="Y coordinate (center if not provided)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Simulate pinch-to-zoom gesture (touch)."""

    async def _pinch():
        connection = await get_connection(session_id, headless, url)

        # Get viewport center if coordinates not provided
        pinch_x = x
        pinch_y = y
        if pinch_x is None or pinch_y is None:
            viewport = connection.page.viewport_size
            if viewport:
                pinch_x = viewport["width"] // 2 if pinch_x is None else pinch_x
                pinch_y = viewport["height"] // 2 if pinch_y is None else pinch_y
            else:
                pinch_x = 500 if pinch_x is None else pinch_x
                pinch_y = 400 if pinch_y is None else pinch_y

        # Use CDP to simulate touch gestures
        cdp = await connection.context.new_cdp_session(connection.page)

        # Simulate pinch gesture
        await cdp.send(
            "Input.synthesizePinchGesture",
            {"x": pinch_x, "y": pinch_y, "scaleFactor": scale, "relativeSpeed": 800, "gestureSourceType": "touch"},
        )

        output_json({"message": "Pinch gesture executed", "scale": scale, "position": {"x": pinch_x, "y": pinch_y}})

    run_async(_pinch())


@app.command()
def fill_form(
    selector: str = typer.Argument(..., help="CSS selector of form"),
    data: str = typer.Option(..., "--data", "-d", help="JSON string or path to JSON/YAML file with form data"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Auto-fill form from JSON string or JSON/YAML file."""
    import yaml

    async def _fill():
        connection = await get_connection(session_id, headless, url)
        try:
            # Load form data - support both inline JSON and file paths
            form_data = None

            # Try parsing as JSON string first
            try:
                form_data = json.loads(data)
            except json.JSONDecodeError:
                pass

            # If not valid JSON, try as file path
            if form_data is None and os.path.exists(data):
                with open(data, "r") as f:
                    if data.endswith(".yaml") or data.endswith(".yml"):
                        form_data = yaml.safe_load(f)
                    else:
                        form_data = json.load(f)

            if form_data is None:
                output_json({"error": f"Invalid data: not valid JSON and file not found: {data}"})
                return

            form_locator = connection.page.locator(selector).first

            # Fill form fields
            filled = []
            for field_name, value in form_data.items():
                # Try multiple selectors
                selectors = [
                    f'input[name="{field_name}"]',
                    f'input[id="{field_name}"]',
                    f'textarea[name="{field_name}"]',
                    f'select[name="{field_name}"]',
                ]

                filled_field = False
                for sel in selectors:
                    try:
                        field = form_locator.locator(sel).first
                        if await field.count() > 0:
                            tag_name = await field.evaluate("el => el.tagName.toLowerCase()")
                            if tag_name == "select":
                                await field.select_option(str(value))
                            else:
                                await field.fill(str(value))
                            filled.append(field_name)
                            filled_field = True
                            break
                    except Exception:
                        continue

                if not filled_field:
                    output_json({"warning": f"Field {field_name} not found"})

            output_json({"message": f"Filled {len(filled)} fields", "fields": filled})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_fill())


@app.command()
def submit_form(
    selector: str = typer.Argument(..., help="CSS selector of form"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Submit a form."""

    async def _submit():
        connection = await get_connection(session_id, headless, url)
        try:
            form_locator = connection.page.locator(selector).first
            await form_locator.evaluate("form => form.submit()")

            # Wait for navigation
            await connection.page.wait_for_load_state("networkidle", timeout=settings.timeout)

            output_json(
                {"message": "Form submitted", "url": connection.page.url, "title": await connection.page.title()}
            )
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_submit())
