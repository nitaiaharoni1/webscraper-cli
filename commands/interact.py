"""Interaction commands."""

import json
import os
from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.browser import save_session_state
from core.output import output_json
from core.settings import settings

app = typer.Typer()


async def _persist_session(connection, session_id, headless):
    """Save session state for headless or named sessions after interaction."""
    effective_headless = headless if headless is not None else settings.headless
    if session_id or effective_headless:
        try:
            current_url = connection.page.url
            # Give redirects a moment to start
            await connection.page.wait_for_timeout(500)
            # If URL changed, a redirect is in progress — wait for it to finish
            if connection.page.url != current_url:
                try:
                    await connection.page.wait_for_load_state("load", timeout=5000)
                except Exception:
                    pass
            # Also settle networkidle for post-redirect content
            try:
                await connection.page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                pass
        except Exception:
            pass
        await save_session_state(connection, session_id or "default")


@app.command()
def click(
    selector: Optional[str] = typer.Argument(None, help="CSS selector (omit when using --by-* options)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    button: str = typer.Option("left", help="Mouse button: left, right, middle"),
    double: bool = typer.Option(False, "--double/--single", help="Perform double click"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector after click"),
    settle_time: int = typer.Option(0, "--settle-time", help="Extra ms to wait after click (useful for SPAs)"),
    by_text: Optional[str] = typer.Option(None, "--by-text", help="Click element by visible text (partial match)"),
    by_role: Optional[str] = typer.Option(None, "--by-role", help="Click element by ARIA role (e.g. button, link)"),
    by_name: Optional[str] = typer.Option(None, "--name", help="Accessible name filter for --by-role"),
    by_test_id: Optional[str] = typer.Option(None, "--by-test-id", help="Click element by data-testid attribute"),
    force: bool = typer.Option(
        False, "--force", help="Force click even if element is not visible (bypasses actionability checks)"
    ),
    focus_first: Optional[str] = typer.Option(
        None,
        "--focus-first",
        help="Focus this selector before clicking (useful for hidden buttons that appear on focus)",
    ),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Click an element by CSS selector or semantic locator.

    Semantic locators are stable alternatives to CSS selectors — they find elements
    by visible text, ARIA role, or test ID rather than fragile class names.

    Examples:
        cli.py interact click ".submit-btn"
        cli.py interact click --by-text "Submit"
        cli.py interact click --by-role button --name "Search"
        cli.py interact click --by-test-id "submit-btn"
    """

    async def _click():
        connection = await get_connection(session_id, headless, url)

        if by_text:
            # Prefer interactive elements (links/buttons) over text containers
            link_loc = connection.page.get_by_role("link", name=by_text)  # type: ignore[arg-type]
            button_loc = connection.page.get_by_role("button", name=by_text)  # type: ignore[arg-type]
            if await link_loc.count() > 0:
                locator = link_loc.first
            elif await button_loc.count() > 0:
                locator = button_loc.first
            else:
                locator = connection.page.get_by_text(by_text, exact=False).first
            label = f"text={by_text!r}"
        elif by_role:
            kwargs = {"name": by_name} if by_name else {}
            locator = connection.page.get_by_role(by_role, **kwargs).first  # type: ignore[arg-type]
            label = f"role={by_role!r}" + (f" name={by_name!r}" if by_name else "")
        elif by_test_id:
            locator = connection.page.get_by_test_id(by_test_id).first
            label = f"test-id={by_test_id!r}"
        elif selector:
            locator = connection.page.locator(selector).first
            label = selector
        else:
            output_json({"error": "Provide a CSS selector or one of --by-text, --by-role, --by-test-id"})
            return

        click_kwargs: dict = {}
        if force:
            click_kwargs["force"] = True

        if focus_first:
            try:
                await connection.page.locator(focus_first).first.focus()
                import asyncio as _aio

                await _aio.sleep(0.3)
            except Exception:
                pass

        try:
            if double:
                await locator.dblclick(**click_kwargs)
            else:
                await locator.click(**click_kwargs)
        except Exception:
            if not force:
                # Auto-retry with force=True when element exists but isn't actionable
                # (common for dynamically revealed buttons, search UIs, etc.)
                try:
                    if double:
                        await locator.dblclick(force=True)
                    else:
                        await locator.click(force=True)
                except Exception:
                    # Final fallback: JS dispatch — bypasses overlay/ad iframe interception
                    try:
                        await locator.evaluate("el => el.click()")
                    except Exception:
                        raise
            else:
                raise

        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)

        await _persist_session(connection, session_id, headless)
        output_json({"message": f"Clicked {label}"})

    run_async(_click())


@app.command()
def type_text(
    text: str,
    selector: Optional[str] = typer.Argument(None, help="CSS selector (omit when using --by-* options)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    delay: Optional[int] = typer.Option(None, help="Delay between keystrokes in milliseconds"),
    clear: bool = typer.Option(False, "--clear/--no-clear", help="Clear the field before typing"),
    by_label: Optional[str] = typer.Option(None, "--by-label", help="Target input by associated <label> text"),
    by_placeholder: Optional[str] = typer.Option(None, "--by-placeholder", help="Target input by placeholder text"),
    by_test_id: Optional[str] = typer.Option(None, "--by-test-id", help="Target input by data-testid attribute"),
    submit: bool = typer.Option(False, "--submit", help="Press Enter after typing (submit form)"),
    settle_time: int = typer.Option(0, "--settle-time", help="Extra ms to wait after typing/submit"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector after typing/submit"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Type text into an element by CSS selector or semantic locator.

    Semantic locators are stable alternatives to CSS selectors — they find inputs
    by their label text, placeholder, or test ID rather than fragile class names.

    Examples:
        cli.py interact type-text "#search" "Playwright"
        cli.py interact type-text --by-label "Email" "user@example.com"
        cli.py interact type-text --by-placeholder "Search..." "query" --submit
        cli.py interact type-text --by-test-id "email-input" "user@example.com"
    """

    async def _type():
        connection = await get_connection(session_id, headless, url)

        if by_label:
            locator = connection.page.get_by_label(by_label).first
            label = f"label={by_label!r}"
        elif by_placeholder:
            locator = connection.page.get_by_placeholder(by_placeholder).first
            label = f"placeholder={by_placeholder!r}"
        elif by_test_id:
            locator = connection.page.get_by_test_id(by_test_id).first
            label = f"test-id={by_test_id!r}"
        elif selector:
            locator = connection.page.locator(selector).first
            label = selector
        else:
            output_json({"error": "Provide a CSS selector or one of --by-label, --by-placeholder, --by-test-id"})
            return

        if clear:
            await locator.clear()

        if delay:
            await locator.type(text, delay=delay)
        else:
            await locator.fill(text)

        if submit:
            await locator.press("Enter")
            # Wait for navigation after submit
            try:
                await connection.page.wait_for_load_state("networkidle", timeout=15000)
            except Exception as e:
                if "Timeout" in str(e):
                    try:
                        await connection.page.wait_for_load_state("load", timeout=10000)
                    except Exception:
                        pass
                else:
                    raise

        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)

        await _persist_session(connection, session_id, headless)

        msg = f"Typed text into {label}"
        if submit:
            msg += " and pressed Enter"
        output_json({"message": msg})

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
        await _persist_session(connection, session_id, headless)
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
    submit: bool = typer.Option(
        False, "--submit", help="Submit the form after filling (clicks submit button or calls form.submit())"
    ),
    settle_time: int = typer.Option(0, "--settle-time", help="Extra ms to wait after submit"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector after submit"),
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

            # Ensure page is fully loaded before querying DOM for labels
            try:
                await connection.page.wait_for_load_state("load", timeout=10000)
            except Exception:
                pass

            form_locator = connection.page.locator(selector).first

            # Fill form fields
            filled = []
            for field_name, value in form_data.items():
                # Try label-based discovery first: find <label> whose text contains field_name,
                # then follow its `for` attribute to the target input id.
                label_for = await connection.page.evaluate(
                    """
                    (name) => {
                        const labels = Array.from(document.querySelectorAll('label'));
                        const match = labels.find(
                            l => l.textContent.trim().toLowerCase().includes(name.toLowerCase())
                        );
                        return match ? (match.htmlFor || null) : null;
                    }
                """,
                    field_name,
                )

                # Build ordered selector list: label-derived id first, then name/id/aria/placeholder
                selectors = []
                if label_for:
                    selectors.append(f"#{label_for}")
                selectors += [
                    f'input[name="{field_name}"]',
                    f'input[id="{field_name}"]',
                    f'textarea[name="{field_name}"]',
                    f'textarea[id="{field_name}"]',
                    f'select[name="{field_name}"]',
                    f'input[aria-label*="{field_name}" i]',
                    f'textarea[aria-label*="{field_name}" i]',
                    f'input[placeholder*="{field_name}" i]',
                    f'textarea[placeholder*="{field_name}" i]',
                    f'[data-testid*="{field_name}" i]',
                ]

                filled_field = False
                for sel in selectors:
                    try:
                        field = form_locator.locator(sel).first
                        if await field.count() > 0:
                            tag_name = await field.evaluate("el => el.tagName.toLowerCase()")
                            input_type = await field.evaluate("el => (el.type || '').toLowerCase()")

                            if tag_name == "select":
                                await field.select_option(str(value))
                            elif input_type in ("checkbox", "radio"):
                                should_check = str(value).lower() not in ("false", "0", "no", "off", "")
                                is_visible = await field.is_visible()
                                if not is_visible:
                                    # Click the label instead of the hidden input
                                    field_id = await field.get_attribute("id")
                                    if field_id:
                                        label_sel = f'label[for="{field_id}"]'
                                        try:
                                            await connection.page.locator(label_sel).click()
                                            filled.append(field_name)
                                            filled_field = True
                                            break
                                        except Exception:
                                            pass
                                await field.set_checked(should_check)
                            else:
                                await field.fill(str(value))
                            filled.append(field_name)
                            filled_field = True
                            break
                    except Exception:
                        continue

                if not filled_field:
                    # Fallback: use Playwright get_by_label for checkboxes/radios missed by selectors
                    try:
                        label_loc = connection.page.get_by_label(field_name, exact=False)
                        if await label_loc.count() > 0:
                            field = label_loc.first
                            input_type = await field.evaluate("el => (el.type || '').toLowerCase()")
                            if input_type in ("checkbox", "radio"):
                                should_check = str(value).lower() not in ("false", "0", "no", "off", "")
                                is_visible = await field.is_visible()
                                if not is_visible:
                                    field_id = await field.get_attribute("id")
                                    if field_id:
                                        await connection.page.locator(f'label[for="{field_id}"]').click()
                                        filled.append(field_name)
                                        filled_field = True
                                if not filled_field:
                                    await field.set_checked(should_check)
                                    filled.append(field_name)
                                    filled_field = True
                    except Exception:
                        pass
                if not filled_field:
                    output_json({"warning": f"Field {field_name} not found"})

            result = {"message": f"Filled {len(filled)} fields", "fields": filled}

            if submit and filled:
                # Try clicking a submit button first, then fall back to form submit event
                submitted = False
                for submit_sel in [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    "button:not([type])",
                    # Also try type="button" with submit-like id/text (React/SPA forms)
                    'button[type="button"][id*="submit" i]',
                    'button[type="button"][class*="submit" i]',
                ]:
                    try:
                        btn = form_locator.locator(submit_sel).first
                        if await btn.count() > 0:
                            try:
                                await btn.click()
                            except Exception:
                                # JS dispatch bypasses overlay/ad iframe interception
                                await btn.evaluate("el => el.click()")
                            submitted = True
                            break
                    except Exception:
                        continue
                if not submitted:
                    # Dispatch submit event — triggers React/Vue/Angular handlers
                    await form_locator.evaluate(
                        "form => form.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}))"
                    )
                # Wait for navigation/settle
                try:
                    await connection.page.wait_for_load_state("networkidle", timeout=15000)
                except Exception as e:
                    if "Timeout" in str(e):
                        try:
                            await connection.page.wait_for_load_state("load", timeout=10000)
                        except Exception:
                            pass
                    else:
                        raise
                if wait_for:
                    await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
                    # Include matched element content in result — captures transient UI (modals, flash messages)
                    try:
                        result["content"] = await connection.page.locator(wait_for).first.inner_text()
                    except Exception:
                        pass
                if settle_time > 0:
                    await connection.page.wait_for_timeout(settle_time)
                result["submitted"] = True
                result["url"] = connection.page.url

            await _persist_session(connection, session_id, headless)
            output_json(result)
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
            try:
                await connection.page.wait_for_load_state("networkidle", timeout=settings.timeout)
            except Exception as e:
                if "Timeout" in str(e):
                    try:
                        await connection.page.wait_for_load_state("load", timeout=10000)
                    except Exception:
                        pass
                else:
                    raise

            output_json(
                {"message": "Form submitted", "url": connection.page.url, "title": await connection.page.title()}
            )
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_submit())
